/*
  Direct-submit handler for the Contact and Leave-a-review forms.

  Submits any <form data-web3forms> to Web3Forms (https://web3forms.com) in
  the background via fetch(), so the visitor never leaves the page and never
  gets bounced to their own email client — they just see an on-brand
  confirmation card (gold check icon, title + message) in place of the form.
  Each form sets its own wording via two attributes:
    data-success-title="..."   — short heading, e.g. "Message sent!"
    data-success-message="..." — the sentence underneath

  SETUP — one step, done once, by Andy:
    1. Go to https://web3forms.com and enter the inbox this should deliver
       to (info@auservices.co.za). No account or password — a free access
       key is emailed instantly.
    2. Paste that key below as WEB3FORMS_ACCESS_KEY, replacing the
       placeholder text.
  Until that's done, both forms still work exactly as before (the mailto:
  fallback below fires instead) and the confirmation card below is not
  shown — a visitor's email client opens instead, so nothing breaks in the
  meantime, but the on-page "thank you" only appears once the key is set.

  Fallback: if this script can't run at all (JS disabled/blocked), each
  form's original action="mailto:..." attribute is left in place, so the
  visitor's email client opens instead — same as before this file existed,
  rather than a submit button that silently does nothing.
*/
(function () {
  var WEB3FORMS_ACCESS_KEY = "PASTE-YOUR-WEB3FORMS-ACCESS-KEY-HERE";

  function isKeySet() {
    return WEB3FORMS_ACCESS_KEY && WEB3FORMS_ACCESS_KEY.indexOf("PASTE-YOUR") !== 0;
  }

  function showResult(form, ok, okMessage, okTitle) {
    var existing = form.querySelector(".form-result");
    if (existing) existing.remove();

    var box = document.createElement("div");
    box.setAttribute("role", "status");
    box.className = "form-result" + (ok ? "" : " form-result--error");

    var icon = document.createElement("span");
    icon.className = "form-result-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.innerHTML = ok
      ? '<i class="ti ti-check"></i>'
      : '<i class="ti ti-alert-triangle"></i>';

    var body = document.createElement("div");
    var title = document.createElement("p");
    title.className = "form-result-title";
    var text = document.createElement("p");
    text.className = "form-result-text";

    if (ok) {
      title.textContent = okTitle || "Thank you!";
      text.textContent = okMessage;
    } else {
      title.textContent = "Something went wrong";
      text.innerHTML =
        'Please try again, or email us directly at ' +
        '<a href="mailto:info@auservices.co.za">info@auservices.co.za</a>.';
    }

    body.appendChild(title);
    body.appendChild(text);
    box.appendChild(icon);
    box.appendChild(body);
    form.appendChild(box);
  }

  function handleSubmit(form) {
    form.addEventListener("submit", function (e) {
      // If the access key hasn't been set up yet, let the form fall through
      // to its normal mailto: action instead of silently failing.
      if (!isKeySet()) return;

      e.preventDefault();

      var btn = form.querySelector('button[type="submit"]');
      var btnLabel = btn ? btn.textContent : "";
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Sending…";
      }

      var data = new FormData(form);
      data.append("access_key", WEB3FORMS_ACCESS_KEY);

      // Auto-populate a reply-to address from whichever email field the
      // form has, if any (the review form doesn't collect one).
      var emailField = form.querySelector('input[type="email"]');
      if (emailField && emailField.value) {
        data.append("replyto", emailField.value);
      }

      fetch("https://api.web3forms.com/submit", {
        method: "POST",
        headers: { Accept: "application/json" },
        body: data,
      })
        .then(function (res) {
          return res.json();
        })
        .then(function (result) {
          if (result && result.success) {
            form.reset();
            showResult(
              form,
              true,
              form.getAttribute("data-success-message") || "Thanks — your message has been sent.",
              form.getAttribute("data-success-title")
            );
          } else {
            showResult(form, false);
          }
        })
        .catch(function () {
          showResult(form, false);
        })
        .finally(function () {
          if (btn) {
            btn.disabled = false;
            btn.textContent = btnLabel;
          }
        });
    });
  }

  var forms = document.querySelectorAll("form[data-web3forms]");
  for (var i = 0; i < forms.length; i++) {
    handleSubmit(forms[i]);
  }
})();
