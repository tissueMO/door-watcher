// ###################################################################
//    JS エントリーポイント
// ###################################################################
import '../../node_modules/popper.js/dist/umd/popper.min.js';
import '../../node_modules/bootstrap/dist/js/bootstrap.min.js';
import '../../node_modules/@coreui/coreui/dist/js/coreui.min.js';
import * as palette from 'google-palette';
const $ = require('../../node_modules/jquery/dist/jquery.min.js');
const Chart = require('../../node_modules/chart.js/dist/Chart.bundle.js');
const API = require('./call-api.js');
const Common = require('./common.js');
const dateformat = require('dateformat');

$(() => {
  if (0 < $('.js-dashboard').length) {
    // ダッシュボード用: 自動で現況取得
    fetchCurrentStatus(true);
  }

  if (0 < $('.js-sidebar-admin').length) {
    // サイドメニュー用: 管理者向け
    adminSideMenu();
  }
});

/**
 * ダッシュボード: 現況を画面に反映
 *
 * @param {boolean} isLoop 完了後に再度時間を置いて取得を行うようにするかどうか
 */
const fetchCurrentStatus = (isLoop) => {
  API.apiRules.fetchCurrentStatus.call({
    success: json => {
      Common.toggleValidMode(true);

      // 既存の現況をすべてクリア
      $('.js-status-item:not(.js-status-item-template)').remove();

      if (json.success === false) {
        // 取得できなかったときはエラー内容を表示する
        throw new Error(`${json.message}`);
      }

      for (const item of json.status) {
        const $newItem = $('.js-status-item-template')
          .clone()
          .removeClass('js-status-item-template d-none');

        if (item.valid === true) {
          $newItem.find('.js-status-invalid').remove();
          if (item.name.includes('男')) {
            $newItem.find('.js-status-valid').addClass('callout-primary');
          } else {
            $newItem.find('.js-status-valid').addClass('callout-danger');
          }
          $newItem.find('.js-status-name').text(item.name);
          $newItem.find('.js-status-rate').text(item.rate100);
          $newItem.find('.js-status-progressbar')
            .attr('aria-valuenow', item.used)
            .attr('aria-valuemax', item.max)
            .css('width', `${item.rate100}%`)
            .addClass(
              (100 <= item.rate100) ? 'bg-danger'
                : (50 <= item.rate100) ? 'bg-warning'
                  : 'bg-success'
            );
          const availableCount = item.max - item.used;
          if (0 < availableCount) {
            $newItem.find('.js-status-available').text(availableCount);
          } else {
            $newItem.find('.js-status-available').text('');
            $newItem.find('.js-status-available-unit').text('無し');
          }
        } else {
          $newItem.find('.js-status-valid').remove();
          if (item.name.includes('男')) {
            $newItem.find('.js-status-invalid').addClass('callout-primary');
          } else {
            $newItem.find('.js-status-invalid').addClass('callout-danger');
          }
          $newItem.find('.js-status-name').text(item.name);
        }

        // 要素追加
        $('.js-dashboard-valid').append($newItem);
      }
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

/**
 * サイドメニュー: 管理者向け機能
 */
const adminSideMenu = () => {
  if (0 < $('.js-log').length) {
    // ログページ用: 自動でログ取得
    fetchLogs();

    // 再取得ボタン
    $('.js-fetch-logs').on('click', () => {
      fetchLogs();
    });
  }

  // サイドメニュー用: 緊急停止 or 再開
  $('.js-action-emergency').on('click', () => {
    API.apiRules.emergency.call({
      success: json => {
        Common.toggleValidMode(json.valid === true);
        alert(`モード [${json.action}] への移行に成功しました。`);
      },
      fail: e => alert('モードの移行に失敗しました。詳細はエラーログをご覧下さい。'),
      final: () => {
        // 完了したら即座に現況を取得
        fetchCurrentStatus(false);
      }
    });
  });
};

/**
 * ログ: ログを画面に反映
 */
const fetchLogs = () => {
  // APIパラメーターをセット
  const beginDate = new Date();
  const endDate = new Date(beginDate.getTime());
  beginDate.setDate(endDate.getDate() - 5);
  const format = 'yyyymmdd';
  const step = 10;
  API.apiRules.fetchLogs.urlSuffix = `/${dateformat(beginDate, format)}/${dateformat(endDate, format)}/${step}`;

  API.apiRules.fetchLogs.call({
    success: json => {
      $('.js-logboard-invalid').hide();
      $('.js-logboard-valid').show();
      $('.js-logboard-container').addClass('flex-fill');

      // 既存の現況をすべてクリア
      $('.js-logboard-canvas:not(.js-logboard-canvas-template)').remove();

      // 系列色を生成
      const colors = palette('mpn65', json.length).map(hex => `#${hex}`);

      // 系列分だけグラフを生成
      json.forEach((item, index) => {
        // テンプレート要素からキャンバスをコピー
        const $newItem = $('.js-logboard-canvas-template')
          .clone()
          .removeClass('js-logboard-canvas-template d-none');

        item.data.datasets[0] = Object.assign(item.data.datasets[0], {
          backgroundColor: `${colors[index]}11`,
          borderColor: colors[index],
          pointRadius: 3,
          pointHitRadius: 6,
          animation: true
        });
        new Chart($newItem, item);

        // 画面上に追加
        $('.js-logboard-canvas-wrapper').append($newItem);
      });
    },
    fail: e => {
      $('.js-logboard-invalid').show();
      $('.js-logboard-valid').hide();
      $('.js-logboard-container').removeClass('flex-fill');
    }
  });
};
