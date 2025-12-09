const USE_MOCK = false;

const mock = {
  alerts: [
    {
      alert_id: "a1",
      type: "Smoke",
      severity: "high",
      apartment_id: "3B",
      room_id: "Room 403",
      status: "open",
      created_at: new Date().toISOString(),
    },
    {
      alert_id: "a2",
      type: "Door",
      severity: "medium",
      apartment_id: "2A",
      room_id: "Entry",
      status: "resolved",
      created_at: new Date(Date.now() - 3600 * 1000).toISOString(),
    },
  ],
  maintenance: [
    {
      request_id: "m1",
      apartment_id: "3B",
      resident_name: "Alice",
      category: "Plumbing",
      status: "in_progress",
      created_at: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
    },
    {
      request_id: "m2",
      apartment_id: "5C",
      resident_name: "Bob",
      category: "Heating",
      status: "pending",
      created_at: new Date(Date.now() - 86400 * 1000).toISOString(),
    },
  ],
  packages: [
    {
      package_id: "p1",
      resident_name: "Chris",
      apartment_id: "2D",
      carrier: "UPS",
      status: "arrived",
      location: "Mailroom A",
      arrived_at: new Date(Date.now() - 3 * 3600 * 1000).toISOString(),
    },
    {
      package_id: "p2",
      resident_name: "Dana",
      apartment_id: "1A",
      carrier: "USPS",
      status: "picked_up",
      location: "Mailroom B",
      arrived_at: new Date(Date.now() - 2 * 86400 * 1000).toISOString(),
    },
  ],
  rooms: [
    {
      room_id: "r1",
      apartment_id: "3B",
      room_name: "Living Room",
      latest_readings: {
        temperature: { timestamp: new Date().toISOString(), value: 23.3 },
      },
    },
    {
      room_id: "r2",
      apartment_id: "3B",
      room_name: "Bedroom",
      latest_readings: {
        temperature: {
          timestamp: new Date(Date.now() - 3600 * 1000).toISOString(),
          value: 21.9,
        },
      },
    },
  ],
  roomHistories: {
    r1: [
      {
        timestamp: new Date(Date.now() - 3 * 3600 * 1000).toISOString(),
        temperature: 22.5,
        smoke: 0,
        noise: 30,
        motion: false,
      },
      {
        timestamp: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
        temperature: 23.0,
        smoke: 0,
        noise: 35,
        motion: true,
      },
      {
        timestamp: new Date(Date.now() - 1 * 3600 * 1000).toISOString(),
        temperature: 23.3,
        smoke: 0,
        noise: 32,
        motion: false,
      },
    ],
    r2: [
      {
        timestamp: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
        temperature: 21.3,
        smoke: 0,
        noise: 20,
        motion: false,
      },
      {
        timestamp: new Date(Date.now() - 1 * 3600 * 1000).toISOString(),
        temperature: 21.9,
        smoke: 0,
        noise: 22,
        motion: false,
      },
    ],
  },
  community: [
    {
      post_id: "c1",
      title: "Free Chair",
      resident_name: "Alice",
      category: "furniture",
      status: "active",
      created_at: new Date(Date.now() - 3600 * 1000).toISOString(),
    },
    {
      post_id: "c2",
      title: "Leftover Pizza",
      resident_name: "Chris",
      category: "food",
      status: "closed",
      created_at: new Date(Date.now() - 3 * 3600 * 1000).toISOString(),
    },
  ],
};

document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupPackagesModal();
  setupRefreshButtons();
  setupLogout();
  loadOverview();
});

function setSection(title, subtitle, sectionId) {
  document.getElementById("section-title").textContent = title;
  document.getElementById("section-subtitle").textContent = subtitle;

  const sections = document.querySelectorAll(".section");
  sections.forEach((s) => s.classList.remove("visible"));
  const target = document.getElementById(sectionId);
  if (target) target.classList.add("visible");
}

function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach((btn) => {
    btn.addEventListener("click", () => {
      navItems.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const section = btn.dataset.section;
      switch (section) {
        case "overview":
          setSection(
            "Overview",
            "Building status at a glance",
            "section-overview"
          );
          loadOverview();
          break;
        case "sensors":
          setSection(
            "Sensors & Rooms",
            "Monitor room sensor readings",
            "section-sensors"
          );
          loadRooms();
          break;
        case "alerts":
          setSection(
            "Alerts",
            "Filter and manage safety alerts",
            "section-alerts"
          );
          loadAlerts();
          break;
        case "maintenance":
          setSection(
            "Maintenance",
            "Manage maintenance requests",
            "section-maintenance"
          );
          loadMaintenance();
          break;
        case "packages":
          setSection(
            "Packages",
            "Track deliveries and pickups",
            "section-packages"
          );
          loadPackages();
          break;
        case "community":
          setSection(
            "Community",
            "Moderate community exchange posts",
            "section-community"
          );
          loadCommunityPosts();
          break;
      }
    });
  });
}

function setupRefreshButtons() {
  const btnAlerts = document.getElementById("btn-alerts-refresh");
  if (btnAlerts) btnAlerts.addEventListener("click", loadAlerts);
  
  const filterAlertsSeverity = document.getElementById("filter-alerts-severity");
  if (filterAlertsSeverity) filterAlertsSeverity.addEventListener("change", loadAlerts);
  
  const filterAlertsStatus = document.getElementById("filter-alerts-status");
  if (filterAlertsStatus) filterAlertsStatus.addEventListener("change", loadAlerts);

  const btnMaint = document.getElementById("btn-maintenance-refresh");
  if (btnMaint) btnMaint.addEventListener("click", loadMaintenance);
  
  const filterMaint = document.getElementById("filter-maintenance-status");
  if (filterMaint) filterMaint.addEventListener("change", loadMaintenance);

  const btnPkg = document.getElementById("btn-packages-refresh");
  if (btnPkg) btnPkg.addEventListener("click", loadPackages);
  
  const filterPkgStatus = document.getElementById("filter-packages-status");
  if (filterPkgStatus) filterPkgStatus.addEventListener("change", loadPackages);

  const btnCommunity = document.getElementById("btn-community-refresh");
  if (btnCommunity) btnCommunity.addEventListener("click", loadCommunityPosts);
  
  const filterCommunityStatus = document.getElementById("filter-community-status");
  if (filterCommunityStatus) filterCommunityStatus.addEventListener("change", loadCommunityPosts);
  
  const filterCommunityCategory = document.getElementById("filter-community-category");
  if (filterCommunityCategory) filterCommunityCategory.addEventListener("change", loadCommunityPosts);
}

function setupLogout() {
  const btn = document.getElementById("logout-btn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    localStorage.removeItem("role");
    window.location.href = "login.html";
  });
}

/* ---------- Overview ---------- */

async function loadOverview() {
  try {
    let data;
    if (USE_MOCK) {
      data = buildOverviewFromMock();
    } else {
      const res = await fetch("/api/admin/overview", {
        credentials: "same-origin"
      });
      if (!res.ok) throw new Error("Failed to load overview");
      const payload = await res.json();
      data = payload.data || payload;
    }

    document.getElementById("metric-alerts-total").textContent =
      data.counts?.alerts_total_today ?? "--";
    document.getElementById("metric-alerts-open").textContent =
      data.counts?.alerts_unresolved ?? "--";
    document.getElementById("metric-maintenance-open").textContent =
      data.counts?.maintenance_open ?? "--";
    document.getElementById("metric-packages-unpicked").textContent =
      data.counts?.packages_unpicked ?? "--";

    const alertsBody = document.getElementById("overview-alerts-body");
    alertsBody.innerHTML = "";
    (data.recent_alerts || []).forEach((alert) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(alert.type)}</td>
        <td>${renderSeverityBadge(alert.severity)}</td>
        <td>${escapeHtml(alert.apartment_id || "")} ${escapeHtml(
        alert.room_id || ""
      )}</td>
        <td>${formatTime(alert.created_at)}</td>
        <td>${renderStatusBadge(alert.status)}</td>
      `;
      alertsBody.appendChild(tr);
    });

    const maintBody = document.getElementById("overview-maintenance-body");
    maintBody.innerHTML = "";
    (data.recent_maintenance || []).forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(item.apartment_id || "")}</td>
        <td>${escapeHtml(item.category || "")}</td>
        <td>${renderStatusBadge(item.status)}</td>
        <td>${formatTime(item.created_at)}</td>
      `;
      maintBody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
  }
}

function buildOverviewFromMock() {
  const todayStr = new Date().toDateString();
  const alertsToday = mock.alerts.filter(
    (a) => new Date(a.created_at).toDateString() === todayStr
  );
  const counts = {
    alerts_total_today: alertsToday.length,
    alerts_unresolved: mock.alerts.filter((a) => a.status === "open").length,
    maintenance_open: mock.maintenance.filter(
      (m) => m.status !== "resolved"
    ).length,
    packages_unpicked: mock.packages.filter(
      (p) => p.status !== "picked_up"
    ).length,
  };
  return {
    counts,
    recent_alerts: [...mock.alerts].slice(-5).reverse(),
    recent_maintenance: [...mock.maintenance].slice(-5).reverse(),
  };
}


let roomsCache = [];

async function loadRooms() {
  try {
    let data;
    if (USE_MOCK) {
      data = mock.rooms;
    } else {
      const res = await fetch("/api/admin/rooms", {
        credentials: "same-origin"
      });
      if (!res.ok) throw new Error("Failed to load rooms");
      data = (await res.json()).data;
    }
    roomsCache = data || [];
    renderRoomsList(roomsCache);

    const searchInput = document.getElementById("rooms-search");
    if (searchInput && !searchInput.dataset.bound) {
      searchInput.dataset.bound = "true";
      searchInput.addEventListener("input", () => {
        const q = searchInput.value.toLowerCase();
        const filtered = roomsCache.filter((room) => {
          const text =
            (room.apartment_id || "") +
            " " +
            (room.room_name || "") +
            " " +
            (room.room_id || "");
          return text.toLowerCase().includes(q);
        });
        renderRoomsList(filtered);
      });
    }
  } catch (err) {
    console.error(err);
  }
}

function renderRoomsList(rooms) {
  const listEl = document.getElementById("rooms-list");
  listEl.innerHTML = "";
  const roomDetailBody = document.getElementById("room-detail-body");
  roomDetailBody.innerHTML =
    '<p class="muted">Select a room on the left to view sensor details.</p>';

  rooms.forEach((room) => {
    const li = document.createElement("li");
    li.className = "list-item-room";
    li.dataset.roomId = room.room_id;

    li.innerHTML = `
      <span class="list-item-room-title">
        ${escapeHtml(room.apartment_id)} - ${escapeHtml(
      room.room_name || room.room_id
    )}
      </span>
      <span class="list-item-room-subtitle">
        Last update: ${formatTime(room.latest_readings?.temperature?.timestamp)}
      </span>
    `;

    li.addEventListener("click", () => {
      document
        .querySelectorAll(".list-item-room")
        .forEach((item) => item.classList.remove("active"));
      li.classList.add("active");
      loadRoomDetail(room.room_id);
    });

    listEl.appendChild(li);
  });
}

async function loadRoomDetail(roomId) {
  const titleEl = document.getElementById("room-detail-title");
  const subtitleEl = document.getElementById("room-detail-subtitle");
  const bodyEl = document.getElementById("room-detail-body");

  const room = roomsCache.find((r) => r.room_id === roomId);
  titleEl.textContent = room
    ? `${room.apartment_id} - ${room.room_name || room.room_id}`
    : "Room Details";
  subtitleEl.textContent = "Latest readings and recent history";

  try {
    let data;
    if (USE_MOCK) {
      data = { readings: mock.roomHistories[roomId] || [] };
    } else {
      const res = await fetch(
        `/api/admin/rooms/${encodeURIComponent(roomId)}/history`,
        { credentials: "same-origin" }
      );
      if (!res.ok) throw new Error("Failed to load room history");
      data = (await res.json()).data;
    }

    const latest = data.readings?.[data.readings.length - 1] || {};

    bodyEl.innerHTML = `
      <div class="grid-2">
        <div>
          <h4>Latest readings</h4>
          <table class="table">
            <tbody>
              <tr><th>Temperature</th><td>${formatValue(
                latest.temperature
              )} °C</td></tr>
              <tr><th>Smoke</th><td>${formatValue(latest.smoke)}</td></tr>
              <tr><th>Noise</th><td>${formatValue(latest.noise)} dB</td></tr>
              <tr><th>Motion</th><td>${latest.motion ? "Detected" : "None"}</td></tr>
            </tbody>
          </table>
        </div>
        <div>
          <h4>Recent history (last entries)</h4>
          <table class="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Temp</th>
                <th>Smoke</th>
                <th>Noise</th>
                <th>Motion</th>
              </tr>
            </thead>
            <tbody>
              ${data.readings
                .slice(-10)
                .map(
                  (r) => `
                <tr>
                  <td>${formatTime(r.timestamp)}</td>
                  <td>${formatValue(r.temperature)}</td>
                  <td>${formatValue(r.smoke)}</td>
                  <td>${formatValue(r.noise)}</td>
                  <td>${r.motion ? "Yes" : "No"}</td>
                </tr>
              `
                )
                .join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    console.error(err);
    bodyEl.innerHTML = `<p class="muted">Failed to load room details.</p>`;
  }
}


async function loadAlerts() {
  try {
    const severity = document.getElementById("filter-alerts-severity").value;
    const status = document.getElementById("filter-alerts-status").value;

    let data;
    if (USE_MOCK) {
      data = mock.alerts.filter((a) => {
        if (severity && a.severity !== severity) return false;
        if (status && a.status !== status) return false;
        return true;
      });
    } else {
      const params = new URLSearchParams();
      if (severity) params.set("severity", severity);
      if (status) params.set("status", status);
      const res = await fetch(`/api/admin/alerts?${params.toString()}`, {
        credentials: "same-origin"
      });
      if (!res.ok) throw new Error("Failed to load alerts");
      data = (await res.json()).data;
    }

    const tbody = document.getElementById("alerts-table-body");
    tbody.innerHTML = "";

    (data || []).forEach((alert) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(alert.type)}</td>
        <td>${renderSeverityBadge(alert.severity)}</td>
        <td>${escapeHtml(alert.apartment_id || "")} ${escapeHtml(
        alert.room_id || ""
      )}</td>
        <td>${formatTime(alert.created_at)}</td>
        <td>${renderStatusBadge(alert.status)}</td>
        <td>
          ${
            alert.status === "open"
              ? `<button class="btn small secondary" data-alert-id="${alert.alert_id}">Resolve</button>`
              : ""
          }
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll("button[data-alert-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.alertId;
        updateAlertStatus(id, "resolved");
      });
    });
  } catch (err) {
    console.error(err);
  }
}

async function updateAlertStatus(alertId, status) {
  try {
    if (USE_MOCK) {
      const a = mock.alerts.find((x) => x.alert_id === alertId);
      if (a) a.status = status;
    } else {
      const res = await fetch(
        `/api/admin/alerts/${encodeURIComponent(alertId)}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ status }),
        }
      );
      if (!res.ok) throw new Error("Failed to update alert status");
      await res.json();
    }
    loadAlerts();
    loadOverview();
  } catch (err) {
    console.error(err);
  }
}


async function loadMaintenance() {
  try {
    const status = document.getElementById(
      "filter-maintenance-status"
    ).value;

    let data;
    if (USE_MOCK) {
      data = mock.maintenance.filter((m) =>
        status ? m.status === status : true
      );
    } else {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      const res = await fetch(
        `/api/admin/maintenance?${params.toString()}`,
        { credentials: "same-origin" }
      );
      if (!res.ok) {
        throw new Error("Failed to load maintenance");
      }
      const responseData = await res.json();
      data = responseData.data || [];
    }

    const tbody = document.getElementById("maintenance-table-body");
    tbody.innerHTML = "";

    (data || []).forEach((req) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(req.apartment_id || "")}</td>
        <td>${escapeHtml(req.resident_name || "")}</td>
        <td>${escapeHtml(req.category || "")}</td>
        <td>${renderStatusBadge(req.status)}</td>
        <td>${formatTime(req.created_at)}</td>
        <td>
          <select class="input" data-request-id="${req.request_id}">
            <option value="pending" ${
              req.status === "pending" ? "selected" : ""
            }>Pending</option>
            <option value="in_progress" ${
              req.status === "in_progress" ? "selected" : ""
            }>In Progress</option>
            <option value="resolved" ${
              req.status === "resolved" ? "selected" : ""
            }>Resolved</option>
          </select>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll("select[data-request-id]").forEach((sel) => {
      sel.addEventListener("change", () => {
        const id = sel.dataset.requestId;
        const newStatus = sel.value;
        updateMaintenanceStatus(id, newStatus);
      });
    });
  } catch (err) {
    console.error(err);
  }
}

async function updateMaintenanceStatus(requestId, status) {
  try {
    if (USE_MOCK) {
      const r = mock.maintenance.find((x) => x.request_id === requestId);
      if (r) r.status = status;
    } else {
      const res = await fetch(
        `/api/admin/maintenance/${encodeURIComponent(requestId)}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ status }),
        }
      );
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        const errorMsg = errorData.error || "Failed to update maintenance status";
        alert(`Error: ${errorMsg}`);
        return;
      }
      
      await res.json();
    }
    
    loadMaintenance();
    loadOverview();
  } catch (err) {
    console.error(err);
    alert(`Error: ${err.message || "Failed to update maintenance status"}`);
  }
}


function setupPackagesModal() {
  const modal = document.getElementById("package-modal");
  const btnNew = document.getElementById("btn-package-new");
  const btnClose = document.getElementById("package-modal-close");
  const btnCancel = document.getElementById("package-modal-cancel");
  const btnSave = document.getElementById("package-modal-save");

  if (btnNew) {
    btnNew.addEventListener("click", () => {
      modal.classList.remove("hidden");
    });
  }

  [btnClose, btnCancel].forEach((btn) => {
    if (btn)
      btn.addEventListener("click", () => {
        modal.classList.add("hidden");
      });
  });

  if (btnSave) {
    btnSave.addEventListener("click", async () => {
      const residentId = document
        .getElementById("package-resident-id")
        .value.trim();
      const carrier = document
        .getElementById("package-carrier")
        .value.trim();
      const location = document
        .getElementById("package-location")
        .value.trim();

      if (!residentId || !carrier || !location) {
        alert("Please fill in all fields.");
        return;
      }

      try {
        if (USE_MOCK) {
          const newPkg = {
            package_id: "mock-" + Date.now(),
            resident_name: `Resident ${residentId}`,
            apartment_id: residentId,
            carrier,
            status: "arrived",
            location,
            arrived_at: new Date().toISOString(),
          };
          mock.packages.unshift(newPkg);
        } else {
          const res = await fetch("/api/admin/packages", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "same-origin",
            body: JSON.stringify({
              resident_id: residentId,
              carrier,
              location,
            }),
          });
          
          if (!res.ok) {
            let errorMsg = "Failed to create package";
            try {
              const errorData = await res.json();
              errorMsg = errorData.error || `Server error (${res.status})`;
            } catch (jsonError) {
              const textError = await res.text().catch(() => "");
              errorMsg = `Server error (${res.status}): ${textError || "Unknown error"}`;
            }
            alert(`Error: ${errorMsg}`);
            return;
          }
          
          await res.json();
        }

        modal.classList.add("hidden");
        document.getElementById("package-resident-id").value = "";
        document.getElementById("package-carrier").value = "";
        document.getElementById("package-location").value = "";
        loadPackages();
        loadOverview();
      } catch (err) {
        console.error(err);
        alert(`Error: ${err.message || "Failed to create package"}`);
      }
    });
  }
}

async function loadPackages() {
  try {
    const status =
      document.getElementById("filter-packages-status").value;

    let data;
    if (USE_MOCK) {
      data = mock.packages.filter((p) =>
        status ? p.status === status : true
      );
    } else {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      const res = await fetch(
        `/api/admin/packages?${params.toString()}`,
        { credentials: "same-origin" }
      );
      if (!res.ok) throw new Error("Failed to load packages");
      data = (await res.json()).data;
    }

    const tbody = document.getElementById("packages-table-body");
    tbody.innerHTML = "";

    (data || []).forEach((pkg) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(pkg.resident_name || "")}</td>
        <td>${escapeHtml(pkg.apartment_id || "")}</td>
        <td>${escapeHtml(pkg.carrier || "")}</td>
        <td>${renderPackageStatusBadge(pkg.status)}</td>
        <td>${escapeHtml(pkg.location || "")}</td>
        <td>${formatTime(pkg.arrived_at)}</td>
        <td>
          ${
            pkg.status === "arrived"
              ? `<button class="btn small secondary" data-action="notify" data-package-id="${pkg.package_id}">Notify</button>`
              : ""
          }
          ${
            pkg.status !== "picked_up"
              ? `<button class="btn small primary" data-action="pickup" data-package-id="${pkg.package_id}">Picked up</button>`
              : ""
          }
          <button class="btn small inline-link" data-action="delete" data-package-id="${pkg.package_id}">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll("button[data-package-id]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const id = btn.dataset.packageId;
        const action = btn.dataset.action;
        
        if (action === "delete") {
          if (confirm("Are you sure you want to delete this package?")) {
            deletePackage(id);
          }
          return;
        }
        
        let newStatus;
        if (action === "notify") {
          newStatus = "notified";
        }
        if (action === "pickup") {
          newStatus = "picked_up";
        }
        
        if (newStatus) {
          updatePackageStatus(id, newStatus);
        }
      });
    });
  } catch (err) {
    console.error(err);
  }
}

async function updatePackageStatus(packageId, status) {
  try {
    if (USE_MOCK) {
      const p = mock.packages.find((x) => x.package_id === packageId);
      if (p) p.status = status;
    } else {
      const res = await fetch(
        `/api/admin/packages/${encodeURIComponent(packageId)}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ status }),
        }
      );
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        const errorMsg = errorData.error || "Failed to update package status";
        alert(`Error: ${errorMsg}`);
        return;
      }
      
      await res.json();
    }
    loadPackages();
    loadOverview();
  } catch (err) {
    console.error(err);
    alert(`Error: ${err.message || "Failed to update package status"}`);
  }
}

async function deletePackage(packageId) {
  try {
    if (USE_MOCK) {
      const idx = mock.packages.findIndex((x) => x.package_id === packageId);
      if (idx >= 0) mock.packages.splice(idx, 1);
    } else {
      const res = await fetch(
        `/api/admin/packages/${encodeURIComponent(packageId)}`,
        {
          method: "DELETE",
          credentials: "same-origin",
        }
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error || "Failed to delete package");
      }
      await res.json();
    }
    loadPackages();
    loadOverview();
  } catch (err) {
    console.error(err);
    alert(`Error: ${err.message || "Failed to delete package"}`);
  }
}


async function loadCommunityPosts() {
  try {
    const status =
      document.getElementById("filter-community-status").value;
    const category =
      document.getElementById("filter-community-category").value;

    let data;
    if (USE_MOCK) {
      data = mock.community.filter((p) => {
        if (status && p.status !== status) return false;
        if (category && p.category !== category) return false;
        return true;
      });
    } else {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      if (category) params.set("category", category);
      const res = await fetch(
        `/api/admin/community/posts?${params.toString()}`,
        { credentials: "same-origin" }
      );
      if (!res.ok) {
        throw new Error("Failed to load community posts");
      }
      const responseData = await res.json();
      data = responseData.data || [];
    }

    const tbody = document.getElementById("community-table-body");
    tbody.innerHTML = "";

    (data || []).forEach((post) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(post.title || "")}</td>
        <td>${escapeHtml(post.resident_name || "")}</td>
        <td>${escapeHtml(post.category || "")}</td>
        <td>${renderCommunityStatusBadge(post.status)}</td>
        <td>${formatTime(post.created_at)}</td>
        <td>
          ${
            post.status === "active"
              ? `<button class="btn small secondary" data-close-id="${post.post_id}">Close</button>`
              : ""
          }
          <button class="btn small inline-link" data-delete-id="${post.post_id}">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll("button[data-close-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.closeId;
        updateCommunityPostStatus(id, "closed");
      });
    });

    tbody.querySelectorAll("button[data-delete-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.deleteId;
        if (confirm("Delete this post? This cannot be undone.")) {
          deleteCommunityPost(id);
        }
      });
    });
  } catch (err) {
    console.error(err);
  }
}

async function updateCommunityPostStatus(postId, status) {
  try {
    if (USE_MOCK) {
      const p = mock.community.find((x) => x.post_id === postId);
      if (p) p.status = status;
    } else {
      const res = await fetch(
        `/api/admin/community/posts/${encodeURIComponent(postId)}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ status }),
        }
      );
      if (!res.ok) throw new Error("Failed to update post status");
      await res.json();
    }
    loadCommunityPosts();
  } catch (err) {
    console.error(err);
  }
}

async function deleteCommunityPost(postId) {
  try {
    if (USE_MOCK) {
      const idx = mock.community.findIndex((x) => x.post_id === postId);
      if (idx >= 0) mock.community.splice(idx, 1);
    } else {
      const res = await fetch(
        `/api/admin/community/posts/${encodeURIComponent(postId)}`,
        { 
          method: "DELETE",
          credentials: "same-origin"
        }
      );
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        const errorMsg = errorData.error || "Failed to delete post";
        alert(`Error: ${errorMsg}`);
        return;
      }
      
      await res.json();
    }
    
    loadCommunityPosts();
  } catch (err) {
    alert(`Error: ${err.message || "Failed to delete post"}`);
  }
}


function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatTime(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString();
}

function formatValue(v) {
  if (v === null || v === undefined) return "";
  if (typeof v === "number") return v.toFixed(2);
  return String(v);
}

function renderSeverityBadge(severity) {
  if (!severity) return "";
  const s = severity.toLowerCase();
  return `<span class="badge ${s}">${s}</span>`;
}

function renderStatusBadge(status) {
  if (!status) return "";
  const s = status.toLowerCase();
  let cls = "";
  if (s === "open" || s === "pending") cls = "badge-status-open";
  if (s === "resolved") cls = "badge-status-resolved";
  if (s === "ignored" || s === "in_progress") cls = "badge-status-ignored";
  return `<span class="badge ${cls}">${s}</span>`;
}

function renderPackageStatusBadge(status) {
  if (!status) return "";
  const s = status.toLowerCase();
  let text = s;
  if (s === "arrived") text = "Arrived";
  if (s === "notified") text = "Notified";
  if (s === "picked_up") text = "Picked up";
  return `<span class="badge">${text}</span>`;
}

function renderCommunityStatusBadge(status) {
  if (!status) return "";
  const s = status.toLowerCase();
  if (s === "active") {
    return `<span class="badge badge-status-open">Active</span>`;
  }
  return `<span class="badge badge-status-ignored">Closed</span>`;
}
