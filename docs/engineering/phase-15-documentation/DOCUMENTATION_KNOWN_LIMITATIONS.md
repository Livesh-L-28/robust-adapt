# Documentation Known Limitations

**Document ID:** `DOC-ENG-P15-006`  
**Phase:** Phase 15 — Documentation & Developer Experience  
**Status:** READY FOR REVIEW  

---

## 1. Documented Gaps & Future Enhancements

1. **Static HTML Site Generation**:
   The documentation currently resides as GitHub Flavored Markdown files in `docs/` and `docs/tutorials/`. A dedicated Sphinx or MkDocs static site build configuration will be added in Phase 17 prior to public beta.
2. **Interactive Jupyter Notebooks**:
   Tutorials are provided as markdown files and standalone `.py` scripts. Future phases will offer pre-configured `.ipynb` notebooks for Google Colab and JupyterLab.
3. **API Cross-Reference Tooling**:
   Automated autodoc / pydoc-markdown generation will be integrated into the CI documentation pipeline for automated publishing.

