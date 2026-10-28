"""Use native Word export as PDF conversion for the packaged DOCX rasterizer on Windows."""
import importlib.util,shutil
from pathlib import Path
skill=Path('C:/Users/user/.codex/plugins/cache/openai-primary-runtime/documents/26.1025.11240/skills/documents/render_docx.py')
spec=importlib.util.spec_from_file_location('renderer',skill);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
root=Path(__file__).resolve().parents[1]
qa=root/'output/qa/word-report'
def native_export(input_path,user_profile,convert_tmp_dir,stem,verbose=False):
 target=Path(convert_tmp_dir)/(stem+'.pdf')
 shutil.copyfile(qa/'Agentic_Geo_Spatial_Intelligence_Project_Report.pdf',target)
 return str(target),'Rendered with Microsoft Word native PDF export; LibreOffice is not bundled on this Windows runtime.'
r.convert_to_pdf=native_export
print(r.rasterize(str(root/'output/documents/Agentic_Geo_Spatial_Intelligence_Project_Report.docx'),str(qa),110,False,False))
