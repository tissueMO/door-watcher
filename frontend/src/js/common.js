// ###################################################################
//    他のモジュールに依存しない関数群
// ###################################################################
const $ = require('../../node_modules/jquery/dist/jquery.min.js');

/**
 * ローディングスピナーを表示
 *
 * @param {boolean} isShow 表示するかどうか
 */
export const viewLoadingSpinner = isShow => {
  if (isShow) {
    $('.js-loading').addClass('show');
  } else {
    $('.js-loading').removeClass('show');
  }
};

/**
 * 現況取得の表示モードを切替
 *
 * @param {boolean} valid 現況取得を表示するかどうか
 */
export const toggleValidMode = valid => {
  if (valid) {
    $('.js-dashboard-valid').show();
    $('.js-dashboard-invalid').hide();
  } else {
    $('.js-dashboard-valid').hide();
    $('.js-dashboard-invalid').show();
  }
};

/**
 * API呼出規約クラス
 */
export class APIRule {
  constructor (apiServerURLBase, url, httpMethod, urlSuffix = '') {
    this.apiServerURLBase = apiServerURLBase;
    this.url = url;
    this.httpMethod = httpMethod;
    this.urlSuffix = urlSuffix;
  }

  call ({ success, fail, final, loadingSpinner = true } = {}) {
    callAPI({
      url: `${this.apiServerURLBase}${this.url}${this.urlSuffix}`,
      httpMethod: this.httpMethod,
      success: success,
      fail: fail,
      final: final,
      loadingSpinner: loadingSpinner
    });
  }
}

/**
 * API呼出用 共通関数
 *
 * @param {string} url APIのURL
 * @param {string} httpMethod HTTPメソッド名
 * @param {function} success 成功時の処理
 * @param {function} fail 失敗時の処理
 * @param {function} final 終了時の共通処理
 */
const callAPI = ({ url, httpMethod = 'GET', success, fail, final, loadingSpinner = true } = {}) => {
  if (loadingSpinner) {
    viewLoadingSpinner(true);
  }

  fetch(url,
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
        viewLoadingSpinner(false);
      }
    });
};
