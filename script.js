document.addEventListener("DOMContentLoaded", () => {
  const taskForm = document.getElementById("task-form");
  const titleInput = document.getElementById("title");
  const deadlineInput = document.getElementById("deadline");
  const prioritySelect = document.getElementById("priority");
  const categoryInput = document.getElementById("category");
  const taskList = document.getElementById("task-list");

  const filterStatus = document.getElementById("filter-status");
  const filterPriority = document.getElementById("filter-priority");
  const filterCategory = document.getElementById("filter-category");

  let tasks = JSON.parse(localStorage.getItem("tasks")) || [];

  function saveTasks() {
    localStorage.setItem("tasks", JSON.stringify(tasks));
  }

  function renderTasks() {
    taskList.innerHTML = "";

    const statusFilter = filterStatus.value;
    const priorityFilter = filterPriority.value;
    const categoryFilter = filterCategory.value.toLowerCase();

    const filtered = tasks.filter((task) => {
      const statusMatch = statusFilter === "all" || task.status === statusFilter;
      const priorityMatch = priorityFilter === "any" || task.priority === priorityFilter;
      const categoryMatch = !categoryFilter || task.category.toLowerCase().includes(categoryFilter);
      return statusMatch && priorityMatch && categoryMatch;
    });

    filtered.forEach((task, index) => {
      const item = document.createElement("div");
      item.classList.add("task-item");
      if (task.priority === "high") item.classList.add("high");
      if (task.priority === "medium") item.classList.add("medium");

      const top = document.createElement("div");
      top.className = "task-title";
      top.textContent = task.title;

      const bottom = document.createElement("div");
      bottom.className = "task-meta";

      const left = document.createElement("div");
      left.className = "meta-left";
      left.innerHTML = `
        <span class="meta-tag">${task.category || "Без категории"}</span>
        <span class="meta-date">${task.deadline || "Без срока"}</span>
      `;

      const right = document.createElement("div");
      right.className = "meta-right";
      right.textContent = task.priority === "high" ? "Высокий" : task.priority === "medium" ? "Средний" : "Обычный";

      bottom.append(left, right);
      item.append(top, bottom);
      taskList.appendChild(item);
    });
  }

  taskForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const task = {
      title: titleInput.value.trim() || "Без названия",
      deadline: deadlineInput.value,
      priority: prioritySelect.value,
      category: categoryInput.value.trim(),
      status: "active",
    };
    tasks.push(task);
    saveTasks();
    renderTasks();
    taskForm.reset();
  });

  [filterStatus, filterPriority, filterCategory].forEach((el) =>
    el.addEventListener("input", renderTasks)
  );

  renderTasks();
});
