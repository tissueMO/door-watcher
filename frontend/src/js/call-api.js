// ###################################################################
//    サーバーAPI呼び出し モジュール
// ###################################################################
const Common = require('./common.js');
const Settings = require('./settings.js');

/**
 * API呼び出し規約
 */
class APIRule {
  constructor (url, httpMethod, urlSuffix = '') {
    this.url = url;
    this.httpMethod = httpMethod;
    this.urlSuffix = urlSuffix;
  }

  call ({ success, fail, final, loadingSpinner = true } = {}) {
    callAPI({
      url: `${this.url}${this.urlSuffix}`,
      httpMethod: this.httpMethod,
      success: success,
      fail: fail,
      final: final,
      loadingSpinner: loadingSpinner
    });
  }
}

/**
 * API呼び出し規約の定義
 */
export const apiRules = {
  // 現況取得
  fetchCurrentStatus: new APIRule('/', 'GET'),

  // ログ取得
  fetchLogs: new APIRule('/logs', 'GET'),

  // 緊急停止 or 再開
  emergency: new APIRule('/emergency', 'PATCH')
};

/**
 * API呼び出し用共通関数
 *
 * @param {string} url APIのURL
 * @param {string} httpMethod HTTPメソッド名
 * @param {function} success 成功時の処理
 * @param {function} fail 失敗時の処理
 * @param {function} final 終了時の共通処理
 */
export const callAPI = ({ url, httpMethod = 'GET', success, fail, final, loadingSpinner = true } = {}) => {
  if (loadingSpinner) {
    Common.viewLoadingSpinner(true);
  }

  fetch(`${Settings.apiServerURLBase}${url}`,
    {
      method: httpMethod,
      mode: 'cors'
    }
  )
    .then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(`${response.status}: サーバー側からエラーが返されました。`);
      }
    })
    .then(json => {
      if (success) {
        success(json);
      }
    })
    .catch(e => {
      if (fail) {
        fail(e);
      }
      console.error(e.message);
    })
    .finally(() => {
      if (final) {
        final();
      }
      if (loadingSpinner) {
        Common.viewLoadingSpinner(false);
      }
    });
};
