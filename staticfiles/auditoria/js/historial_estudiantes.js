document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("audit-search");
  const clearBtn = document.getElementById("audit-clear");
  const table = document.getElementById("audit-table");
  if (!input || !table) return;

  const rows = Array.from(table.querySelectorAll("tbody tr"));

  function normalize(text) {
    return (text || "").toLowerCase();
  }

  function filterTable(value) {
    const q = normalize(value);
    rows.forEach((row) => {
      const text = normalize(row.textContent);
      const match = text.indexOf(q) !== -1;
      row.style.display = match ? "" : "none";
    });
  }

  input.addEventListener("input", function () {
    filterTable(this.value);
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      input.value = "";
      filterTable("");
    });
  }

  // Aplica filtro inicial si viene desde el servidor
  const serverVal = input.getAttribute("data-server-value") || "";
  if (serverVal) {
    filterTable(serverVal);
  }
});
