// ###################################################################
//    JS エントリーポイント
// ###################################################################
import '../../node_modules/popper.js/dist/umd/popper.min.js';
import '../../node_modules/bootstrap/dist/js/bootstrap.min.js';
import '../../node_modules/@coreui/coreui/dist/js/coreui.min.js';
const $ = require('../../node_modules/jquery/dist/jquery.min.js');

$(() => {
  // ページIDに応じて読み込むJSを分岐する
  const pageID = $('body').attr('id');
  const suffix = /^page-(.*)$/g.exec(pageID)[1];
  require(`./${suffix}.js`);

  // 管理者用サイドバーの有無に応じて読み込むJSを分岐する
  const hasSidebarForAdmin = $('.sidebar').attr('id') === 'sidebar-admin';
  if (hasSidebarForAdmin) {
    require('./sidebar-admin.js');
  }
});
