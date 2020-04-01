// ###################################################################
//    会議室チェッカー
// ###################################################################
const $ = require('jquery/dist/jquery.min');
const Common = require('./common.js');
const API = require('./call-api-room.js');

/**
 * 前回取得した現況情報 (キャッシュ用)
 */
let previousFetchedStatusCache;

$(() => {
  if (0 < $('.js-dashboard').length) {
    // ダッシュボード用: 自動で現況取得
    fetchCurrentStatus(true);
  }
});

/**
 * ダッシュボード: 現況を画面に反映
 *
 * @param {boolean} isLoop 完了後に再度時間を置いて取得を行うようにするかどうか
 */
export const fetchCurrentStatus = (isLoop) => {
  API.apiRules.fetchCurrentStatus.call({
    loadingSpinner: false,
    success: json => {
      Common.toggleValidMode(true);

      if (JSON.stringify(json) === previousFetchedStatusCache) {
        console.info('取得した現況情報が前回の結果と合致しているため画面更新をスキップします。');
        return;
      }

      // 今回の現況情報を保管
      previousFetchedStatusCache = JSON.stringify(json);

      // 画面変更を行っていることを表すために一時的にローディングスピナーを出す
      Common.viewLoadingSpinner(true);

      // 一定時間経過後に画面更新
      setTimeout(() => {
        Common.viewLoadingSpinner(false);

        // 既存の現況をすべてクリア
        $('.js-status-item:not(.js-status-item-template)').remove();

        for (const item of json) {
          const $newItem = $('.js-status-item-template')
            .clone()
            .removeClass('js-status-item-template d-none');

          $newItem.find('.js-status-name').text(`${item.name} 会議室`);
          $newItem.find('.js-status-invalid').remove();
          $newItem.find('.js-status-valid').addClass(
            item.is_use ? 'callout-danger' : 'callout-success'
          );
          $newItem.find('.js-status-available').text(
            item.is_use ? '使用中' : '空室'
          );
          $newItem.find('.js-status-available-icon').text(
            item.is_use ? 'no_meeting_room' : 'meeting_room'
          );

          // 要素追加
          $('.js-dashboard-valid').append($newItem);
        }
      }, 250);
    },
    fail: e => {
      Common.toggleValidMode(false);
    },
    final: () => {
      if (isLoop) {
        // 定期的に現況を取得
        setTimeout(() => fetchCurrentStatus(true), 5000);
      }
    }
  });
};
