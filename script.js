function renderMoC(data) {
  const moc = data.hsr.memory_of_chaos;
  if (!moc || !moc.floor_data) return;

  const container = document.getElementById("moc-content");
  container.innerHTML = "";

  const floor = moc.floor_data;

  const card = document.createElement("div");
  card.classList.add("moc-card");

  // Header
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

  // Node 1
  nodeRow.appendChild(createNode("Node 1", floor.first_half));

  // Node 2
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

async function loadStats() {
  try {
    const response = await fetch("data/stats.json");
    if (!response.ok) throw new Error("Failed to fetch JSON");

    const data = await response.json();
    const sr = data.hsr;

    // Avatar
    const avatarContainer = document.getElementById("avatar");
    avatarContainer.innerHTML = `
            <img src="${sr.avatar}" alt="Avatar" style="
              width: 100%;
              height: 100%;
              border-radius: 50%;
              object-fit: cover;
            ">
          `;

    // Main card info
    document.querySelector(".nickname").innerText = sr.nickname;
    document.querySelector(".server-level").innerText =
      `NA | Level ${sr.level}`;

    const statsContainer = document.querySelector(".stats");
    statsContainer.innerHTML = `
        <div class="stat">Active Days<br><strong>${sr.active_days}</strong></div>
        <div class="stat">Achievements<br><strong>${sr.achievements}</strong></div>
        <div class="stat">Characters<br><strong>${sr.avatar_count}</strong></div>
        <div class="stat">Chests<br><strong>${sr.chest_count}</strong></div>
      `;

    // Trailblaze mini card
    const stamina = sr.stamina ?? 0;
    const train = sr.current_train_score ?? 0; // make sure your JSON has this
    document.getElementById("stamina").innerHTML =
      `Trailblaze Power: <strong>${stamina}/300</strong>`;
    document.getElementById("train").innerHTML =
      `Daily Training: <strong>${train}/500</strong>`;
    document.getElementById("logged-in").innerHTML =
      `Logged In Today: <strong>${train != 0 ? "Yes" : "No"}</strong>`;

    renderMoC(data);
  } catch (err) {
    console.error(err);
    document.getElementById("card").innerText = "Failed to load stats.";
  }
}

function pityColor(pity) {
  // Clamp pity between 1 and 90
  pity = Math.max(1, Math.min(90, pity));

  if (pity <= 45) {
    // interpolate between low (#57bb8a) and mid (#ffd666)
    const t = (pity - 1) / (45 - 1);
    return lerpColor("#57bb8a", "#ffd666", t);
  } else {
    // interpolate between mid (#ffd666) and high (#e67c73)
    const t = (pity - 45) / (90 - 45);
    return lerpColor("#ffd666", "#e67c73", t);
  }
}

// Helper to interpolate two hex colors
function lerpColor(a, b, t) {
  const ah = parseInt(a.slice(1), 16),
    bh = parseInt(b.slice(1), 16);
  const ar = (ah >> 16) & 0xff,
    ag = (ah >> 8) & 0xff,
    ab = ah & 0xff;
  const br = (bh >> 16) & 0xff,
    bg = (bh >> 8) & 0xff,
    bb = bh & 0xff;
  const rr = Math.round(ar + (br - ar) * t),
    rg = Math.round(ag + (bg - ag) * t),
    rb = Math.round(ab + (bb - ab) * t);
  return `rgb(${rr},${rg},${rb})`;
}

async function loadTimeline() {
  try {
    const response = await fetch("data/sheet.csv");
    const text = await response.text();

    const rows = text.trim().split("\n").slice(1); // remove header

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

    // Sort newest first
    entries.reverse();

    const tooltip = document.getElementById("tooltip");
    const grid = document.getElementById("pull-grid");

    entries.forEach((entry) => {
      // generate icon url automatically
      let iconURL = "";

      if (entry.id >= 20000) {
        iconURL = `https://stardb.gg/api/static/StarRailResWebp/icon/light_cone/${entry.id}.webp`;
      } else {
        iconURL = `https://stardb.gg/api/static/StarRailResWebp/icon/character/${entry.id}.webp`;
      }

      // Determine result text
      let resultText = "";
      let resultClass = "";

      if (entry.result === "W") {
        resultText = "Win";
        resultClass = "win";
      } else if (entry.result === "L") {
        resultText = "Lose";
        resultClass = "lose";
      } else if (entry.result === "G") {
        resultText = "Guaranteed";
        resultClass = "guaranteed";
      }

      const container = document.createElement("div");
      container.classList.add("pull-item");

      const img = document.createElement("img");
      img.src = iconURL;

      // Tooltip text
      const tooltipText = `${entry.character} • ${entry.banner}\nResult: ${resultText}\nPity: ${entry.pity}\nDate: ${entry.date}`;

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

      switch (resultText.toLowerCase()) {
        case "win":
          img.style.borderColor = "green";
          break;
        case "lose":
          img.style.borderColor = "red";
          break;
        case "guaranteed":
          img.style.borderColor = "gold";
          break;
        default:
          img.style.borderColor = "grey";
      }

      // Pity badge
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

loadStats();
loadTimeline();
