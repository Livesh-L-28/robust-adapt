"""Vectorized Streaming Decision Tree (VectorizedHoeffdingTree).

Mathematical formulation specified in DOC-DES-P6-003 and DOC-DES-P6-009 (Algorithms 1 & 2).
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from adaptive_ml.core.constants import EPS_DIV
from adaptive_ml.core.exceptions import ValidationError
from adaptive_ml.core.types import FloatArray1D, FloatArray2D, IntArray1D
from adaptive_ml.core.validation import check_array_2d, check_labels_1d, check_sample_weights


class _Node:
    """Base node in Hoeffding decision tree."""

    __slots__ = ("node_id", "depth")

    def __init__(self, node_id: int, depth: int) -> None:
        self.node_id = int(node_id)
        self.depth = int(depth)


class _SplitNode(_Node):
    """Internal decision node splitting on a single feature attribute."""

    __slots__ = ("split_feature", "split_threshold", "left_child", "right_child")

    def __init__(
        self,
        node_id: int,
        depth: int,
        split_feature: int,
        split_threshold: float,
        left_child: _Node,
        right_child: _Node,
    ) -> None:
        super().__init__(node_id, depth)
        self.split_feature = int(split_feature)
        self.split_threshold = float(split_threshold)
        self.left_child = left_child
        self.right_child = right_child


class _LeafNode(_Node):
    """Leaf node maintaining sufficient statistics tensors."""

    __slots__ = ("stats", "n_samples", "last_split_check", "class_counts")

    def __init__(self, node_id: int, depth: int, n_features: int, n_bins: int, n_classes: int) -> None:
        super().__init__(node_id, depth)
        # 3D Tensor: shape (n_features, n_bins, n_classes)
        self.stats = np.zeros((n_features, n_bins, n_classes), dtype=np.float64)
        self.class_counts = np.zeros(n_classes, dtype=np.float64)
        self.n_samples: float = 0.0
        self.last_split_check: float = 0.0


class VectorizedHoeffdingTree:
    """Vectorized Streaming Decision Tree classifier executing Hoeffding-bound splitting.

    Maintains contiguous 3D sufficient statistics arrays per leaf node, enabling fast
    mini-batch vector accumulation via NumPy without single-instance dictionary iteration.

    Parameters
    ----------
    n_features : int
        Dimensionality of input feature space.
    n_classes : int
        Number of discrete target classes.
    grace_period : int, default=200
        Number of instances accumulated at a leaf between split evaluation checks.
    delta : float, default=1e-5
        Hoeffding split confidence parameter (1 - delta confidence).
    tau_tie : float, default=0.05
        Tie-breaking split threshold for near-identical candidate attributes.
    n_bins : int, default=32
        Number of quantile discretization bins per feature.
    min_leaf_samples : int, default=10
        Minimum samples required in child partitions for a valid split.
    max_depth : int, default=20
        Maximum tree depth limit to prevent infinite split recursion.
    """

    def __init__(
        self,
        n_features: int,
        n_classes: int,
        grace_period: int = 200,
        delta: float = 1e-5,
        tau_tie: float = 0.05,
        n_bins: int = 32,
        min_leaf_samples: int = 10,
        max_depth: int = 20,
    ) -> None:
        if n_features <= 0:
            raise ValidationError(f"n_features must be >= 1, got {n_features}")
        if n_classes < 2:
            raise ValidationError(f"n_classes must be >= 2, got {n_classes}")
        if grace_period <= 0:
            raise ValidationError(f"grace_period must be >= 1, got {grace_period}")
        if delta <= 0.0 or delta >= 1.0:
            raise ValidationError(f"delta must be in (0, 1), got {delta}")
        if n_bins < 2:
            raise ValidationError(f"n_bins must be >= 2, got {n_bins}")

        self.n_features = int(n_features)
        self.n_classes = int(n_classes)
        self.grace_period = int(grace_period)
        self.delta = float(delta)
        self.tau_tie = float(tau_tie)
        self.n_bins = int(n_bins)
        self.min_leaf_samples = int(min_leaf_samples)
        self.max_depth = int(max_depth)

        self._next_node_id: int = 0
        self.root: _Node = self._create_leaf(depth=0)
        self.bin_edges: Optional[np.ndarray] = None  # Shape (n_features, n_bins - 1)
        self.total_samples_seen: int = 0

    def _create_leaf(self, depth: int) -> _LeafNode:
        leaf = _LeafNode(
            node_id=self._next_node_id,
            depth=depth,
            n_features=self.n_features,
            n_bins=self.n_bins,
            n_classes=self.n_classes,
        )
        self._next_node_id += 1
        return leaf

    def _init_bin_edges(self, X: np.ndarray) -> None:
        """Initialize fixed quantile split thresholds from initial feature distribution."""
        self.bin_edges = np.zeros((self.n_features, self.n_bins - 1), dtype=np.float64)
        quantiles = np.linspace(0.0, 1.0, self.n_bins + 1)[1:-1]
        for j in range(self.n_features):
            col = X[:, j]
            edges = np.quantile(col, quantiles)
            # Ensure strictly non-decreasing edges
            if np.all(edges == edges[0]):
                edges = np.linspace(np.min(col) - 1.0, np.max(col) + 1.0, self.n_bins + 1)[1:-1]
            self.bin_edges[j] = edges

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "VectorizedHoeffdingTree":
        """Incrementally update the tree with a streaming mini-batch of instances."""
        X_val = check_array_2d(X, expected_dim=self.n_features, name="X")
        n_samples = X_val.shape[0]
        y_val = check_labels_1d(y, expected_len=n_samples, n_classes=self.n_classes, name="y")
        w_val = check_sample_weights(sample_weight, expected_len=n_samples, name="sample_weight")
        if w_val is None:
            w_val = np.ones(n_samples, dtype=np.float64)

        # Initialize quantile bin edges on first batch
        if self.bin_edges is None:
            self._init_bin_edges(X_val)

        # Route each sample in batch to its destination leaf node
        leaf_nodes = self._route_batch_to_leaves(X_val)
        unique_leaves = set(leaf_nodes)

        # Vectorized accumulation per leaf
        for leaf in unique_leaves:
            mask = [node is leaf for node in leaf_nodes]
            mask_arr = np.array(mask, dtype=bool)
            X_leaf = X_val[mask_arr]
            y_leaf = y_val[mask_arr]
            w_leaf = w_val[mask_arr]
            n_leaf_batch = X_leaf.shape[0]

            # Vectorized feature discretization
            assert self.bin_edges is not None
            for j in range(self.n_features):
                bin_indices = np.digitize(X_leaf[:, j], self.bin_edges[j])
                bin_indices = np.clip(bin_indices, 0, self.n_bins - 1)

                for c in range(self.n_classes):
                    c_mask = (y_leaf == c)
                    if np.any(c_mask):
                        bins_c = bin_indices[c_mask]
                        weights_c = w_leaf[c_mask]
                        np.add.at(leaf.stats[j, :, c], bins_c, weights_c)

            # Update sample counts
            batch_weight_sum = float(np.sum(w_leaf))
            leaf.n_samples += batch_weight_sum
            for c in range(self.n_classes):
                leaf.class_counts[c] += float(np.sum(w_leaf[y_leaf == c]))

            # Periodically evaluate Hoeffding split check
            if (leaf.n_samples - leaf.last_split_check) >= self.grace_period:
                if leaf.depth < self.max_depth:
                    self._attempt_split(leaf)
                leaf.last_split_check = leaf.n_samples

        self.total_samples_seen += n_samples
        return self

    def _route_sample(self, x: np.ndarray, current: _Node) -> _LeafNode:
        """Recursively route single instance down to a leaf node."""
        while isinstance(current, _SplitNode):
            if x[current.split_feature] <= current.split_threshold:
                current = current.left_child
            else:
                current = current.right_child
        assert isinstance(current, _LeafNode)
        return current

    def _route_batch_to_leaves(self, X: np.ndarray) -> List[_LeafNode]:
        """Route each instance in batch to its active leaf node."""
        return [self._route_sample(X[i], self.root) for i in range(X.shape[0])]

    def _attempt_split(self, leaf: _LeafNode) -> bool:
        """Evaluate Hoeffding bound for candidate splits at given leaf node."""
        n_u = leaf.n_samples
        if n_u < self.min_leaf_samples * 2:
            return False

        # Current leaf Gini impurity
        probs = leaf.class_counts / (n_u + EPS_DIV)
        gini_current = 1.0 - float(np.sum(probs ** 2))
        if gini_current <= 1e-6:
            return False  # Pure node

        assert self.bin_edges is not None
        best_gain_1 = -1.0
        best_feat_1 = -1
        best_bin_1 = -1

        best_gain_2 = -1.0

        for j in range(self.n_features):
            # Cumulative sums across split bins for feature j: shape (n_bins - 1, n_classes)
            left_counts = np.cumsum(leaf.stats[j, : self.n_bins - 1, :], axis=0)
            right_counts = leaf.class_counts - left_counts

            n_L = np.sum(left_counts, axis=1)
            n_R = np.sum(right_counts, axis=1)

            # Valid split mask: ensure child leaves satisfy min_leaf_samples
            valid_mask = (n_L >= self.min_leaf_samples) & (n_R >= self.min_leaf_samples)
            if not np.any(valid_mask):
                continue

            # Vectorized Gini for all thresholds
            with np.errstate(divide="ignore", invalid="ignore"):
                p_L = left_counts / (n_L[:, np.newaxis] + EPS_DIV)
                p_R = right_counts / (n_R[:, np.newaxis] + EPS_DIV)
                gini_L = 1.0 - np.sum(p_L ** 2, axis=1)
                gini_R = 1.0 - np.sum(p_R ** 2, axis=1)
                gini_split = (n_L / n_u) * gini_L + (n_R / n_u) * gini_R
                gains = gini_current - gini_split

            gains[~valid_mask] = -1.0
            max_bin_j = int(np.argmax(gains))
            max_gain_j = float(gains[max_bin_j])

            if max_gain_j > best_gain_1:
                best_gain_2 = best_gain_1
                best_gain_1 = max_gain_j
                best_feat_1 = j
                best_bin_1 = max_bin_j
            elif max_gain_j > best_gain_2:
                best_gain_2 = max_gain_j

        if best_feat_1 < 0 or best_gain_1 <= 0.0:
            return False

        # Hoeffding bound computation
        R_G = 1.0 - (1.0 / self.n_classes)
        epsilon_H = math.sqrt((R_G ** 2 * math.log(1.0 / self.delta)) / (2.0 * n_u))
        delta_G = best_gain_1 - max(0.0, best_gain_2)

        # Splitting Decision Rule
        if (delta_G > epsilon_H) or (epsilon_H < self.tau_tie):
            threshold = float(self.bin_edges[best_feat_1, best_bin_1])
            self._split_leaf(leaf, best_feat_1, threshold)
            return True

        return False

    def _split_leaf(self, leaf: _LeafNode, split_feature: int, split_threshold: float) -> None:
        """Replace leaf node with internal split node and two child leaves."""
        left_child = self._create_leaf(depth=leaf.depth + 1)
        right_child = self._create_leaf(depth=leaf.depth + 1)

        # Initialize child class priors from partition
        left_counts = np.sum(leaf.stats[split_feature, : np.digitize(split_threshold, self.bin_edges[split_feature]) + 1, :], axis=0)
        right_counts = leaf.class_counts - left_counts
        left_child.class_counts = np.maximum(0.0, left_counts)
        left_child.n_samples = float(np.sum(left_child.class_counts))
        right_child.class_counts = np.maximum(0.0, right_counts)
        right_child.n_samples = float(np.sum(right_child.class_counts))

        new_split = _SplitNode(
            node_id=leaf.node_id,
            depth=leaf.depth,
            split_feature=split_feature,
            split_threshold=split_threshold,
            left_child=left_child,
            right_child=right_child,
        )

        if self.root is leaf:
            self.root = new_split
        else:
            self._replace_node(self.root, leaf, new_split)

    def _replace_node(self, parent: _Node, target: _Node, replacement: _Node) -> bool:
        """Traverse tree to replace target leaf node with new split node."""
        if not isinstance(parent, _SplitNode):
            return False
        if parent.left_child is target:
            parent.left_child = replacement
            return True
        if parent.right_child is target:
            parent.right_child = replacement
            return True
        return self._replace_node(parent.left_child, target, replacement) or self._replace_node(
            parent.right_child, target, replacement
        )

    def predict_proba(self, X: np.ndarray) -> FloatArray2D:
        """Predict class posterior probabilities for input instances."""
        X_val = check_array_2d(X, expected_dim=self.n_features, name="X")
        n_samples = X_val.shape[0]
        probs = np.zeros((n_samples, self.n_classes), dtype=np.float64)

        leaf_nodes = self._route_batch_to_leaves(X_val)
        for i in range(n_samples):
            leaf = leaf_nodes[i]
            counts = leaf.class_counts + 1.0  # Laplace smoothing
            probs[i] = counts / np.sum(counts)

        return np.ascontiguousarray(probs)

    def predict(self, X: np.ndarray) -> IntArray1D:
        """Predict target class labels."""
        probs = self.predict_proba(X)
        return np.ascontiguousarray(np.argmax(probs, axis=1), dtype=np.int64)

    def state_dict(self) -> Dict[str, Any]:
        """Serialize tree topology and sufficient statistics."""
        def _serialize_node(node: _Node) -> Dict[str, Any]:
            if isinstance(node, _SplitNode):
                return {
                    "type": "split",
                    "node_id": node.node_id,
                    "depth": node.depth,
                    "split_feature": node.split_feature,
                    "split_threshold": node.split_threshold,
                    "left": _serialize_node(node.left_child),
                    "right": _serialize_node(node.right_child),
                }
            elif isinstance(node, _LeafNode):
                return {
                    "type": "leaf",
                    "node_id": node.node_id,
                    "depth": node.depth,
                    "n_samples": node.n_samples,
                    "class_counts": node.class_counts.tolist(),
                    "stats": node.stats.tolist(),
                }
            raise ValidationError(f"Unknown node type: {type(node)}")

        return {
            "n_features": self.n_features,
            "n_classes": self.n_classes,
            "grace_period": self.grace_period,
            "delta": self.delta,
            "tau_tie": self.tau_tie,
            "n_bins": self.n_bins,
            "min_leaf_samples": self.min_leaf_samples,
            "max_depth": self.max_depth,
            "total_samples_seen": self.total_samples_seen,
            "bin_edges": self.bin_edges.tolist() if self.bin_edges is not None else None,
            "tree": _serialize_node(self.root),
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore tree topology and statistics."""
        self.n_features = int(state["n_features"])
        self.n_classes = int(state["n_classes"])
        self.grace_period = int(state["grace_period"])
        self.delta = float(state["delta"])
        self.tau_tie = float(state["tau_tie"])
        self.n_bins = int(state["n_bins"])
        self.min_leaf_samples = int(state["min_leaf_samples"])
        self.max_depth = int(state["max_depth"])
        self.total_samples_seen = int(state["total_samples_seen"])
        self.bin_edges = np.array(state["bin_edges"], dtype=np.float64) if state["bin_edges"] is not None else None

        def _deserialize_node(d: Dict[str, Any]) -> _Node:
            if d["type"] == "split":
                return _SplitNode(
                    node_id=int(d["node_id"]),
                    depth=int(d["depth"]),
                    split_feature=int(d["split_feature"]),
                    split_threshold=float(d["split_threshold"]),
                    left_child=_deserialize_node(d["left"]),
                    right_child=_deserialize_node(d["right"]),
                )
            elif d["type"] == "leaf":
                leaf = _LeafNode(
                    node_id=int(d["node_id"]),
                    depth=int(d["depth"]),
                    n_features=self.n_features,
                    n_bins=self.n_bins,
                    n_classes=self.n_classes,
                )
                leaf.n_samples = float(d["n_samples"])
                leaf.class_counts = np.array(d["class_counts"], dtype=np.float64)
                leaf.stats = np.array(d["stats"], dtype=np.float64)
                return leaf
            raise ValidationError(f"Unknown node type: {d['type']}")

        self.root = _deserialize_node(state["tree"])

