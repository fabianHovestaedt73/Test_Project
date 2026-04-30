/**
 * Task Manager
 * Add, complete, filter, and delete tasks. Persists to localStorage.
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'taskmanager.tasks.v1';

    /** @type {{id: string, text: string, completed: boolean}[]} */
    let tasks = [];
    let currentFilter = 'all';

    // DOM references
    const form = document.getElementById('task-form');
    const input = document.getElementById('task-input');
    const list = document.getElementById('task-list');
    const emptyState = document.getElementById('empty-state');
    const taskCount = document.getElementById('task-count');
    const clearCompletedBtn = document.getElementById('clear-completed');
    const filterButtons = document.querySelectorAll('.filter-btn');

    // ---------- Persistence ----------
    function loadTasks() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            tasks = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(tasks)) tasks = [];
        } catch {
            tasks = [];
        }
    }

    function saveTasks() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
        } catch {
            /* ignore quota / privacy errors */
        }
    }

    // ---------- Helpers ----------
    function generateId() {
        return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    }

    function getFilteredTasks() {
        switch (currentFilter) {
            case 'active':
                return tasks.filter(t => !t.completed);
            case 'completed':
                return tasks.filter(t => t.completed);
            default:
                return tasks;
        }
    }

    // ---------- Rendering ----------
    function render() {
        const filtered = getFilteredTasks();
        list.replaceChildren();

        filtered.forEach(task => {
            list.appendChild(createTaskElement(task));
        });

        // Empty state
        emptyState.hidden = filtered.length !== 0;
        if (filtered.length === 0) {
            if (tasks.length === 0) {
                emptyState.textContent = 'No tasks yet. Add one above to get started.';
            } else if (currentFilter === 'active') {
                emptyState.textContent = 'No active tasks. Nice work!';
            } else {
                emptyState.textContent = 'No completed tasks yet.';
            }
        }

        // Counter
        const remaining = tasks.filter(t => !t.completed).length;
        taskCount.textContent =
            `${remaining} ${remaining === 1 ? 'task' : 'tasks'} remaining`;

        // Clear completed visibility
        const hasCompleted = tasks.some(t => t.completed);
        clearCompletedBtn.hidden = !hasCompleted;
    }

    function createTaskElement(task) {
        const li = document.createElement('li');
        li.className = 'task-item' + (task.completed ? ' completed' : '');
        li.dataset.id = task.id;

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'task-checkbox';
        checkbox.checked = task.completed;
        checkbox.id = `task-${task.id}`;
        checkbox.setAttribute(
            'aria-label',
            task.completed ? 'Mark as not completed' : 'Mark as completed'
        );
        checkbox.addEventListener('change', () => toggleTask(task.id));

        const label = document.createElement('label');
        label.className = 'task-text';
        label.htmlFor = checkbox.id;
        label.textContent = task.text; // textContent prevents XSS

        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'delete-btn';
        deleteBtn.setAttribute('aria-label', `Delete task: ${task.text}`);
        deleteBtn.innerHTML = '&times;';
        deleteBtn.addEventListener('click', () => deleteTask(task.id));

        li.append(checkbox, label, deleteBtn);
        return li;
    }

    // ---------- Actions ----------
    function addTask(text) {
        const trimmed = text.trim();
        if (!trimmed) return;

        tasks.unshift({
            id: generateId(),
            text: trimmed,
            completed: false,
        });
        saveTasks();
        render();
    }

    function toggleTask(id) {
        const task = tasks.find(t => t.id === id);
        if (!task) return;
        task.completed = !task.completed;
        saveTasks();
        render();
    }

    function deleteTask(id) {
        tasks = tasks.filter(t => t.id !== id);
        saveTasks();
        render();
    }

    function clearCompleted() {
        tasks = tasks.filter(t => !t.completed);
        saveTasks();
        render();
    }

    function setFilter(filter) {
        currentFilter = filter;
        filterButtons.forEach(btn => {
            const active = btn.dataset.filter === filter;
            btn.classList.toggle('is-active', active);
            btn.setAttribute('aria-pressed', String(active));
        });
        render();
    }

    // ---------- Event wiring ----------
    form.addEventListener('submit', e => {
        e.preventDefault();
        addTask(input.value);
        input.value = '';
        input.focus();
    });

    clearCompletedBtn.addEventListener('click', clearCompleted);

    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => setFilter(btn.dataset.filter));
    });

    // ---------- Init ----------
    loadTasks();
    render();
})();
