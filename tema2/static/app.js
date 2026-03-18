const statusEl = document.getElementById("status");
const gamesBody = document.getElementById("games-body");
const createForm = document.getElementById("create-form");
const editForm = document.getElementById("edit-form");
const editDialog = document.getElementById("edit-dialog");
const cancelEditBtn = document.getElementById("cancel-edit");

const createCategorySelect = document.getElementById("create-category");
const editCategorySelect = document.getElementById("edit-category");
const filterCategory = document.getElementById("filter-category");
const filterCompleted = document.getElementById("filter-completed");

const applyFiltersBtn = document.getElementById("apply-filters");
const clearFiltersBtn = document.getElementById("clear-filters");

function setStatus(message) {
    statusEl.textContent = message;
}

async function api(path, options = {}) {
    const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });

    if (response.status === 204) {
        return null;
    }

    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(body.error || "Unknown API error");
    }
    return body;
}

function buildPayload(form) {
    const data = new FormData(form);
    const ratingValue = data.get("rating");

    return {
        title: data.get("title").trim(),
        platform: data.get("platform").trim(),
        genre: data.get("genre").trim(),
        hours_played: Number(data.get("hours_played")),
        rating: ratingValue ? Number(ratingValue) : null,
        completed: data.get("completed") === "true",
        category_id: Number(data.get("category_id")),
    };
}

function rowTemplate(game) {
    const completedClass = game.completed ? "tag-ok" : "tag-no";
    const completedText = game.completed ? "Yes" : "No";
    const ratingText = game.rating == null ? "-" : game.rating.toFixed(1);

    return `
        <tr>
            <td>${game.id}</td>
            <td>${game.title}</td>
            <td>${game.platform}</td>
            <td>${game.genre}</td>
            <td>${game.hours_played}</td>
            <td>${ratingText}</td>
            <td class="${completedClass}">${completedText}</td>
            <td>${game.category_name ?? "-"}</td>
            <td>
                <div class="actions">
                    <button data-edit="${game.id}" type="button">Edit</button>
                    <button data-delete="${game.id}" class="muted" type="button">Delete</button>
                </div>
            </td>
        </tr>
    `;
}

async function loadCategories() {
    const categories = await api("/api/categories");

    const options = categories
        .map((category) => `<option value="${category.id}">${category.name}</option>`)
        .join("");

    createCategorySelect.innerHTML = options;
    editCategorySelect.innerHTML = options;
    filterCategory.innerHTML = `<option value="">All categories</option>${options}`;
}

function buildQuery() {
    const params = new URLSearchParams();
    if (filterCompleted.value) {
        params.set("completed", filterCompleted.value);
    }
    if (filterCategory.value) {
        params.set("category_id", filterCategory.value);
    }

    const query = params.toString();
    return query ? `/api/games?${query}` : "/api/games";
}

async function loadGames() {
    setStatus("Loading games...");
    try {
        const games = await api(buildQuery());
        gamesBody.innerHTML = games.map(rowTemplate).join("");
        setStatus(`Loaded ${games.length} game(s)`);
    } catch (error) {
        setStatus(error.message);
    }
}

createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = buildPayload(createForm);

    try {
        await api("/api/games", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        createForm.reset();
        createForm.completed.value = "false";
        await loadGames();
        setStatus("Game created successfully");
    } catch (error) {
        setStatus(error.message);
    }
});

gamesBody.addEventListener("click", async (event) => {
    const editId = event.target.getAttribute("data-edit");
    const deleteId = event.target.getAttribute("data-delete");

    if (editId) {
        try {
            const game = await api(`/api/games/${editId}`);
            editForm.id.value = game.id;
            editForm.title.value = game.title;
            editForm.platform.value = game.platform;
            editForm.genre.value = game.genre;
            editForm.hours_played.value = game.hours_played;
            editForm.rating.value = game.rating ?? "";
            editForm.completed.value = String(game.completed);
            editForm.category_id.value = game.category_id;
            editDialog.showModal();
        } catch (error) {
            setStatus(error.message);
        }
    }

    if (deleteId) {
        const shouldDelete = confirm(`Delete game #${deleteId}?`);
        if (!shouldDelete) {
            return;
        }

        try {
            await api(`/api/games/${deleteId}`, { method: "DELETE" });
            await loadGames();
            setStatus("Game deleted");
        } catch (error) {
            setStatus(error.message);
        }
    }
});

editForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = editForm.id.value;
    const payload = buildPayload(editForm);

    try {
        await api(`/api/games/${id}`, {
            method: "PUT",
            body: JSON.stringify(payload),
        });
        editDialog.close();
        await loadGames();
        setStatus("Game updated");
    } catch (error) {
        setStatus(error.message);
    }
});

cancelEditBtn.addEventListener("click", () => {
    editDialog.close();
});

applyFiltersBtn.addEventListener("click", loadGames);
clearFiltersBtn.addEventListener("click", async () => {
    filterCompleted.value = "";
    filterCategory.value = "";
    await loadGames();
});

(async function bootstrap() {
    try {
        await loadCategories();
        await loadGames();
    } catch (error) {
        setStatus(error.message);
    }
})();
