/* =========================
   Navigation
========================= */

function showPage(pageId) {
  document.querySelectorAll(".page").forEach((p) => {
    p.classList.remove("active");
  });

  document.getElementById(pageId).classList.add("active");
}

/* =========================
   Memory of Chaos
========================= */

function renderMoC(data) {
  const moc = data?.hsr?.memory_of_chaos;
  if (!moc || !moc.floor_data) return;

  const container = document.getElementById("moc-content");
  container.innerHTML = "";

  const floor = moc.floor_data;

  const card = document.createElement("div");
  card.classList.add("moc-card");

  const header = document.createElement("div");
  header.classList.add("moc-header");

  const floorTitle = document.createElement("div");
  floorTitle.classList.add("moc-floor");
  floorTitle.textContent = floor.floor;

  const cycles = document.createElement("div");
  cycles.classList.add("moc-cycles");
  cycles.textContent = `Cycles: ${floor.cycles} | ⭐ ${moc.total_stars}`;

  header.appendChild(floorTitle);
  header.appendChild(cycles);
  card.appendChild(header);

  const nodeRow = document.createElement("div");
  nodeRow.classList.add("moc-node-row");

  nodeRow.appendChild(createNode("Node 1", floor.first_half));
  nodeRow.appendChild(createNode("Node 2", floor.second_half));

  card.appendChild(nodeRow);
  container.appendChild(card);
}

function createNode(title, characters) {
  const node = document.createElement("div");
  node.classList.add("moc-node");

  const nodeTitle = document.createElement("div");
  nodeTitle.classList.add("moc-node-title");
  nodeTitle.textContent = title;

  const avatarRow = document.createElement("div");
  avatarRow.classList.add("moc-avatars");

  characters.forEach((char) => {
    const wrapper = document.createElement("div");
    wrapper.classList.add("moc-avatar");

    const img = document.createElement("img");
    img.src = `https://stardb.gg/api/static/StarRailResWebp/icon/character/${char.id}.webp`;

    const badge = document.createElement("div");
    badge.classList.add("eidolon-badge");
    badge.textContent = `E${char.eidolon}`;

    wrapper.appendChild(img);
    wrapper.appendChild(badge);
    avatarRow.appendChild(wrapper);
  });

  node.appendChild(nodeTitle);
  node.appendChild(avatarRow);

  return node;
}

/* =========================
   HSR Profile Render
========================= */

function renderHSR(data) {
  const sr = data.hsr;
  if (!sr) return;

  const container = document.getElementById("hsr-profile");

  container.innerHTML = `
    <div class="card">
      <div class="avatar">
        <img src="${sr.avatar}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">
      </div>
      <div class="nickname">${sr.nickname}</div>
      <div class="server-level">NA | Level ${sr.level}</div>
      <div class="stats">
        <div class="stat">Active Days<br><strong>${sr.active_days}</strong></div>
        <div class="stat">Achievements<br><strong>${sr.achievements}</strong></div>
        <div class="stat">Characters<br><strong>${sr.avatar_count}</strong></div>
        <div class="stat">Chests<br><strong>${sr.chest_count}</strong></div>
      </div>
    </div>
  `;

  // Trailblaze card
  const trail = document.getElementById("trailblaze-card");

  trail.innerHTML = `
    <div class="mini-card">
      <h3>Today's Status</h3>
      <div class="line">Trailblaze Power: <strong>${sr.stamina ?? 0}/300</strong></div>
      <div class="line">Daily Training: <strong>${sr.current_train_score ?? 0}/500</strong></div>
      <div class="line">Logged In Today: <strong>${(sr.current_train_score ?? 0) != 0 ? "Yes" : "No"}</strong></div>
    </div>
  `;
}

/* =========================
   Genshin Render
========================= */

function renderGenshin(data) {
  const gi = data.genshin;
  if (!gi) return;

  const container = document.getElementById("genshin-profile");

  container.innerHTML = `
    <div class="card">
      <div class="avatar">
        <img src="${gi.avatar}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">
      </div>
      <div class="nickname">${gi.nickname}</div>
      <div class="server-level">AR ${gi.level}</div>
      <div class="stats">
        <div class="stat">Achievements<br><strong>${gi.achievements}</strong></div>
        <div class="stat">Active Days<br><strong>${gi.active_days}</strong></div>
        <div class="stat">Characters<br><strong>${gi.avatar_count}</strong></div>
        <div class="stat">Oculus<br><strong>${gi.oculus}</strong></div>
        <div class="stat">Chests<br><strong>${gi.chest_count}</strong></div>
      </div>
    </div>
  `;

  // Notes card
  const notes = document.getElementById("genshin-notes");

  notes.innerHTML = `
    <div class="mini-card">
      <h3>Today's Status</h3>
      <div class="line">Resin: <strong>${gi.resin ?? 0}/200</strong></div>
      <div class="line">Daily Tasks: <strong>${gi.daily_task ?? 0}/4</strong></div>
      <div class="line">Logged In Today: <strong>${(gi.daily_task ?? 0) != 0 ? "Yes" : "No"}</strong></div>
    </div>
  `;
}

/* =========================
   Pull Timeline
========================= */

function pityColor(pity) {
  pity = Math.max(1, Math.min(90, pity));

  if (pity <= 45) {
    const t = (pity - 1) / 44;
    return lerpColor("#57bb8a", "#ffd666", t);
  } else {
    const t = (pity - 45) / 45;
    return lerpColor("#ffd666", "#e67c73", t);
  }
}

function lerpColor(a, b, t) {
  const ah = parseInt(a.slice(1), 16);
  const bh = parseInt(b.slice(1), 16);

  const ar = (ah >> 16) & 0xff;
  const ag = (ah >> 8) & 0xff;
  const ab = ah & 0xff;

  const br = (bh >> 16) & 0xff;
  const bg = (bh >> 8) & 0xff;
  const bb = bh & 0xff;

  const rr = Math.round(ar + (br - ar) * t);
  const rg = Math.round(ag + (bg - ag) * t);
  const rb = Math.round(ab + (bb - ab) * t);

  return `rgb(${rr},${rg},${rb})`;
}

async function loadTimeline() {
  try {
    const response = await fetch("data/sheet.csv");
    const text = await response.text();

    const rows = text.trim().split("\n").slice(1);
    const entries = rows.map((row) => {
      const [date, banner, id, character, glw, pity] = row.split(",");
      return {
        date: date.trim(),
        banner: banner.trim(),
        id: parseInt(id.trim()),
        character: character.trim(),
        result: glw.trim(),
        pity: parseInt(pity.trim()),
      };
    });

    entries.reverse();

    const grid = document.getElementById("pull-grid");
    const tooltip = document.getElementById("tooltip");

    grid.innerHTML = "";

    entries.forEach((entry) => {
      const container = document.createElement("div");
      container.classList.add("pull-item");

      const img = document.createElement("img");

      if (entry.id >= 20000) {
        img.src = `https://stardb.gg/api/static/StarRailResWebp/icon/light_cone/${entry.id}.webp`;
      } else {
        img.src = `https://stardb.gg/api/static/StarRailResWebp/icon/character/${entry.id}.webp`;
      }

      const tooltipText =
        `${entry.character} • ${entry.banner}\n` +
        `Result: ${entry.result}\n` +
        `Pity: ${entry.pity}\n` +
        `Date: ${entry.date}`;

      img.addEventListener("mouseenter", (e) => {
        tooltip.style.display = "block";
        tooltip.innerText = tooltipText;
      });

      img.addEventListener("mousemove", (e) => {
        tooltip.style.left = e.pageX + 10 + "px";
        tooltip.style.top = e.pageY + 10 + "px";
      });

      img.addEventListener("mouseleave", () => {
        tooltip.style.display = "none";
      });

      const badge = document.createElement("span");
      badge.classList.add("pull-badge");
      badge.innerText = entry.pity;
      badge.style.background = pityColor(entry.pity);

      container.appendChild(img);
      container.appendChild(badge);
      grid.appendChild(container);
    });
  } catch (err) {
    console.error("Failed to load timeline:", err);
  }
}

/* =========================
   Load Everything
========================= */

function renderHome(data) {
  const sr = data.hsr;
  const gi = data.genshin;

  const homeHSR = document.getElementById("home-hsr");
  const homeGI = document.getElementById("home-genshin");

  if (sr) {
    homeHSR.innerHTML = `
      <div class="card">
        <h2>Honkai: Star Rail</h2>
        <div class="nickname">${sr.nickname}</div>
        <div>Level ${sr.level}</div>
        <div>⭐ MoC Stars: ${sr.memory_of_chaos?.total_stars ?? 0}</div>
        <div>Trailblaze Power: ${sr.stamina ?? 0}/300</div>
      </div>
    `;
  }

  if (gi) {
    homeGI.innerHTML = `
      <div class="card">
        <h2>Genshin Impact</h2>
        <div class="nickname">${gi.nickname}</div>
        <div>AR ${gi.level}</div>
        <div>Achievements: ${gi.achievements}</div>
      </div>
    `;
  }
}

async function loadStats() {
  try {
    const response = await fetch("data/stats.json");
    if (!response.ok) throw new Error("Failed to fetch JSON");

    const data = await response.json();

    renderHome(data);
    renderHSR(data);
    renderMoC(data);
    renderGenshin(data);
  } catch (err) {
    console.error(err);
  }
}

loadStats();
loadTimeline();
