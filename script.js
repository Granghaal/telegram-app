const tg = window.Telegram.WebApp;
tg.expand();

const taskForm = document.getElementById("task-form");
const taskList = document.getElementById("task-list");
const filterPriority = document.getElementById("filter-priority");
const filterCategory = document.getElementById("filter-category");
const resetFilters = document.getElementById("reset-filters");

let tasks = [];

taskForm.addEventListener("submit", (e) => {
  e.preventDefault();

  const title = document.getElementById("title").value.trim();
  const category = document.getElementById("category").value;
  const priority = document.getElementById("priority").value;
  const deadline = document.getElementById("deadline").value;

  if (!title) return;

  const task = {
    title,
    category: category || "Без категории",
    priority: priority || "Обычный",
    deadline: deadline || "Не указано",
    author: tg.initDataUnsafe?.user?.username || "неизвестен",
    created_at: new Date().toISOString(),
  };

  tasks.push(task);
  saveToTelegram(task);
  renderTasks();

  taskForm.reset();
});

function saveToTelegram(task) {
  const data = {
    type: "new_task",
    payload: task,
  };
  tg.sendData(JSON.stringify(data));
}

function renderTasks() {
  taskList.innerHTML = "";

  const filtered = tasks.filter((t) => {
    return (
      (!filterPriority.value || t.priority === filterPriority.value) &&
      (!filterCategory.value || t.category === filterCategory.value)
    );
  });

  filtered.forEach((t) => {
    const el = document.createElement("div");
    el.className = "task";

    el.innerHTML = `
      <div class="task-title">${t.title}</div>
      <div class="task-meta">
        <span class="meta category">${t.category}</span>
        <span class="meta priority ${t.priority.toLowerCase()}">${t.priority}</span>
        <span class="meta deadline">${t.deadline}</span>
        <span class="meta author">@${t.author}</span>
      </div>
    `;

    taskList.appendChild(el);
  });
}

filterPriority.addEventListener("change", renderTasks);
filterCategory.addEventListener("change", renderTasks);
resetFilters.addEventListener("click", () => {
  filterPriority.value = "";
  filterCategory.value = "";
  renderTasks();
});
