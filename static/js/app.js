const form = document.getElementById("form");
const urlInput = document.getElementById("url-input");
const dateInput = document.getElementById("date-input");
const errorDiv = document.getElementById("error");
const resultDiv = document.getElementById("result");
const loadingOverlay = document.getElementById("loading-overlay");

const today = new Date().toISOString().slice(0, 10);
dateInput.value = today;
dateInput.min = today;

function showLoading(on) {
  loadingOverlay.classList.toggle("hidden", !on);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorDiv.textContent = "";
  resultDiv.innerHTML = "";

  const url = urlInput.value.trim();
  const dateVal = dateInput.value;

  if (!url || !dateVal) return;

  showLoading(true);

  try {
    const res = await fetch("/api/menu", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ url, date: dateVal }),
});

    const data = await res.json();

    if (!res.ok) {
      errorDiv.textContent = data.error || "An unknown error occurred.";
      resultDiv.innerHTML = "";
      return;
    }

    renderResult(data);
  } catch (err) {
    errorDiv.textContent = "Fetch error: " + err.message;
    resultDiv.innerHTML = "";
  } finally {
    showLoading(false);
  }
});

function renderResult(data) {
  const container = document.createElement("div");
  container.className = "card";

  if (data.error) {
    container.innerHTML = "<p><strong>Chyba:</strong> " + data.error + "</p>";
    if (data.raw_response) {
      const pre = document.createElement("pre");
      pre.textContent = JSON.stringify(data.raw_response, null, 2);
      container.appendChild(pre);
    }
    resultDiv.innerHTML = "";
    resultDiv.appendChild(container);
    return;
  }

  const restaurant = data.restaurant_name || "Neznámá restaurace";
  const dateText = data.date || "-";
  const day = data.day_of_week || "-";
  const source = data.source_url || "";
  const items = data.menu_items || [];
  const cached = data.cached === true;

  container.innerHTML = `
    <h2>${restaurant} ${cached ? "<small>(z cache)</small>" : ""}</h2>
    <p><strong>Datum:</strong> ${dateText} (${day})</p>
    <p><strong>Zdroj:</strong> <a href="${source}" target="_blank">${source}</a></p>
  `;

  const list = document.createElement("div");
  if (!items.length) {
    list.innerHTML = "<p><em>No menu found for the selected date.</em></p>";
  } else {
    items.forEach((item) => {
      const div = document.createElement("div");
      div.className = "menu-item";

      const category = item.category || "";
      const name = item.name || "";
      const price =
        item.price !== null && item.price !== undefined
          ? item.price + " Kč"
          : "—";
      const weight = item.weight || "";

      div.innerHTML = `
        <strong>${category}</strong><br/>
        <span>${name}</span><br/>
        <span>${weight ? weight + " | " : ""}${price}</span>
      `;

      if (item.allergens && item.allergens.length) {
        const alDiv = document.createElement("div");
        alDiv.innerHTML = "<small>Alergeny:</small> ";
        item.allergens.forEach((a) => {
          const b = document.createElement("span");
          b.className = "badge";
          b.textContent = a;
          alDiv.appendChild(b);
        });
        div.appendChild(alDiv);
      }

      list.appendChild(div);
    });
  }

  container.appendChild(list);

  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(data, null, 2);
  container.appendChild(pre);

  resultDiv.innerHTML = "";
  resultDiv.appendChild(container);
}
