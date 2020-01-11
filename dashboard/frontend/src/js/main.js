import '../../node_modules/popper.js/dist/umd/popper.min.js';
import '../../node_modules/bootstrap/dist/js/bootstrap.min.js';
import '../../node_modules/@coreui/coreui/dist/js/coreui.min.js';
const $ = require('../../node_modules/jquery/dist/jquery.min.js');

$(() => {
  /**
   * 現況取得の表示モードを切替
   */
  const toggleValidMode = valid => {
    $('.js-dashboard-valid').hide();
    $('.js-dashboard-invalid').show();
  };

  /**
   * 現況取得
   */
  const fetchCurrentStatus = () => {
    fetch('/functions/fetch/status', {
      method: 'GET'
    }).then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(`${response.status}: サーバー側からエラーが返されました。`);
      }
    }).then(json => {
      toggleValidMode(true);
      applyCurrentStatus(json);
    }).catch(e => {
      toggleValidMode(false);
      console.error(e.message);
    });

    // 定期的に現況を取得
    setTimeout(fetchCurrentStatus, 5000);
  };
  fetchCurrentStatus();

  /**
   * 現況を画面に反映
   *
   * @param {string} json 現況取得結果
   */
  const applyCurrentStatus = json => {
    for (const item of json.status) {
      const $newItem = $('.js-dashboard-item-template')
        .clone()
        .removeClass('js-dashboard-item-template d-none');

      if (item.invalid !== true) {
        $newItem.find('.js-status-invalid').remove();
        $newItem.find('.js-status-name').text(item.name);
        $newItem.find('.js-status-rate').text(item.rate100);
        $newItem.find('.js-status-progressbar')
          .attr('aria-valuenow', item.current)
          .attr('aria-valuemax', item.max)
          .css('width', `${item.rate100}%`)
          .addClass(
            (100 <= item.rate100) ? 'bg-danger'
              : (50 <= item.rate100) ? 'bg-warning'
                : 'bg-success'
          );
        $newItem.find('js-status-available').text(item.max - item.current);
      } else {
        $newItem.find('.js-status-valid').remove();
        $newItem.find('.js-status-name').text(item.name);
      }

      // 要素追加
      $('.js-dashboard-valid').append($newItem);
    }
  };

  /**
   * ログ取得
   */
  $('.js-fetch-logs').on('click', () => {
    fetch('/functions/fetch/log', {
      method: 'GET'
    }).then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(`${response.status}: サーバー側からエラーが返されました。`);
      }
    }).then(json => {
      // TODO: 画面表示
    }).catch(e => {
      console.error(e.message);
    });
  });

  /**
   * 緊急停止/再開
   */
  $('.js-action-emergency').on('click', () => {
    fetch('/functions/action/emergency', {
      method: 'POST'
    }).then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(`${response.status}: サーバー側からエラーが返されました。`);
      }
    }).then(json => {
      toggleValidMode(json.valid === true);
      alert(`モード [${json.action}] への移行に成功しました。`);
    }).catch(e => {
      console.error(e.message);
      alert('モードの移行に失敗しました。詳細はエラーログをご覧下さい。');
    });
  });
});
