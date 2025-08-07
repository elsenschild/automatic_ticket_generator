from PyInstaller.utils.hooks import collect_submodules, copy_metadata

hiddenimports = collect_submodules("requests")
datas = copy_metadata("requests")
