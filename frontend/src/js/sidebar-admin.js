// ###################################################################
//    管理者向け サイドバー
// ###################################################################
const $ = require('jquery/dist/jquery.min');
const Common = require('./common.js');
const toilet = require('./toilet.js');
const APIToilet = require('./call-api-toilet.js');

$(() => {
  if (0 < $('.js-sidebar-admin').length) {
    // サイドメニュー用: 管理者向け
    adminSideMenu();
  }
});

/**
 * サイドメニュー: 管理者向け機能
 */
const adminSideMenu = () => {
  if (0 < $('.js-log').length) {
    // ログページ用: 自動でログ取得
    toilet.fetchLogs();

    // 再取得ボタン
    $('.js-fetch-logs').on('click', () => {
      toilet.fetchLogs();
    });
  }

  // サイドメニュー用: 緊急停止 or 再開
  $('.js-action-emergency').on('click', () => {
    APIToilet.apiRules.emergency.call({
      success: json => {
        Common.toggleValidMode(json.valid === true);
        alert(`モード [${json.action}] への移行に成功しました。`);
      },
      fail: e => alert('モードの移行に失敗しました。詳細はエラーログをご覧下さい。')
    });
  });
};
