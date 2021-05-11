from configs import workspace_define
from utils import unicode_util

unicode_blocks = unicode_util.load_blocks_db(workspace_define.unicode_blocks_db_path)
unicode_block_name_translations = unicode_util.load_block_name_translations(workspace_define.unicode_block_name_translations_file_path)
