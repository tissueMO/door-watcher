// ###################################################################
//    会議室チェッカー: サーバーAPI呼出規約
// ###################################################################
const Common = require('./common.js');
const Settings = require('./settings-room.js');

/**
 * API呼び出し規約の定義
 */
export const apiRules = {
  // 現況取得
  fetchCurrentStatus: new Common.APIRule(Settings.apiServerURLBase, '/', 'GET')
};
