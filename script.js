function addTask() {
  const input = document.getElementById("taskInput");
  const task = input.value.trim();
  if (task !== "") {
    const li = document.createElement("li");
    li.textContent = task;
    document.getElementById("taskList").appendChild(li);
    input.value = "";
  }
}
