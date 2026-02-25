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
        <img src="${sr.avatar_url}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">
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
        <img src="${gi.avatar_url}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">
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

    const latestFiveStar = entries[0];

    if (latestFiveStar) {
      const latestContainer = document.getElementById("home-latest-pull");

      let img_src;

      if (latestFiveStar.id >= 20000) {
        img_src = `https://stardb.gg/api/static/StarRailResWebp/icon/light_cone/${latestFiveStar.id}.webp`;
      } else {
        img_src = `https://stardb.gg/api/static/StarRailResWebp/icon/character/${latestFiveStar.id}.webp`;
      }

      latestContainer.innerHTML = `
            <div class="card">
            <div class="avatar">
                <img src="${img_src}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">
            </div>
            <h2>Latest HSR 5★ Pull</h2>
            <p class="latest-name">${latestFiveStar.character}</p>
                <div class="latest-meta">
                    <p>Pity: ${latestFiveStar.pity}</p>
                    <p>Date: ${latestFiveStar.date}</p>
                </div>
            </div>
        `;
    }
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
