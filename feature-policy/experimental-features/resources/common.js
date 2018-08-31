const url_base = "/feature-policy/experimental-features/resources/";
window.messageResponseCallback = null;

function setFeatureState(iframe, feature, origins) {
    iframe.setAttribute("allow", `${feature} ${origins};`);
}

// Returns a promise which is resolved when the <iframe> is navigated to |url|
// and "load" handler has been called.
function loadUrlInIframe(iframe, url) {
  return new Promise((resolve) => {
    iframe.addEventListener("load", resolve);
    iframe.src = url;
  });
}

// Posts |message| to |target| and resolves the promise with the response coming
// back from |target|.
function sendMessageAndGetResponse(target, message) {
  return new Promise((resolve) => {
    window.messageResponseCallback = resolve;
    target.postMessage(message, "*");
  });
}


function onMessage(e) {
  if (window.messageResponseCallback) {
    window.messageResponseCallback(e.data);
    window.messageResponseCallback = null;
  }
}

window.addEventListener("message", onMessage);



// Waits for |load_timeout| before resolving the promise. It will resolve the
// promise sooner if a message event with |e.data.id| of |id| is received.
// If the promise is resolved with a timeout the response is |false|. Otherwise,
// the response (argument passed on to the |then|) is the value of
// |e.data.contents|.
function waitForMessageOrTimeout(t, id, load_timeout) {
  let callback = null, did_resolve = false;
  function resolvePromise(e) {
    if (e && e.data && e.data.id && e.data.id === id && !did_resolve) {
      callback(e.data.contents);
      window.removeEventListener("message", resolvePromise);
    } else {
      callback(false);
    }
    did_resolve = true;
  }
  t.step_timeout(resolvePromise, load_timeout);
  window.addEventListener("message", resolvePromise);
  return new Promise( (resolve) => {
    callback = resolve;
  });
}

function createIframe(container, attributes) {
  var new_iframe = document.createElement("iframe");
  for (attr_name in attributes)
    new_iframe.setAttribute(attr_name, attributes[attr_name]);
  container.appendChild(new_iframe);
  return new_iframe;
}
