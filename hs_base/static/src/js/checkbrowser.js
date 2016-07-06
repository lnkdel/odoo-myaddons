var canRun = 0;
var ua = navigator.userAgent;
if(ua.indexOf("Firefox") != -1||ua.indexOf("Chrome") != -1||ua.indexOf("Safari") != -1){
    canRun = 1;
}

if(canRun == 0){
    window.location.href = '/hs_base/static/src/html/browser.html';
}
