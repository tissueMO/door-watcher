// ###################################################################
//    他のモジュールに依存しない関数群
// ###################################################################
const $ = require('../../node_modules/jquery/dist/jquery.min.js');

/**
 * ローディングスピナーを表示
 * @param {boolean} 表示するかどうか
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
