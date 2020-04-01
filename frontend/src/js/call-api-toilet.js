// ###################################################################
//    トイレチェッカー: サーバーAPI呼出規約
// ###################################################################
const Common = require('./common.js');
const Settings = require('./settings-toilet.js');

/**
 * API呼び出し規約の定義
 */
export const apiRules = {
  // 現況取得
  fetchCurrentStatus: new Common.APIRule(Settings.apiServerURLBase, '/', 'GET'),

  // ログ取得
  fetchLogs: new Common.APIRule(Settings.apiServerURLBase, '/logs/', 'GET'),

  // 緊急停止 or 再開
  emergency: new Common.APIRule(Settings.apiServerURLBase, '/emergency/', 'PATCH')
};
