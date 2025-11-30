// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// State Management
let tasks = [];
let currentResults = null;

// DOM Elements
let elements = {};

function initializeElements() {
    elements = {
        // Tabs
        tabButtons: document.querySelectorAll('.tab-button'),
        singleTab: document.getElementById('single-tab'),
        bulkTab: document.getElementById('bulk-tab'),
        
        // Forms
        singleTaskForm: document.getElementById('single-task-form'),
        bulkTaskForm: document.getElementById('bulk-task-form'),
        
        // Strategy & Role
        strategySelect: document.getElementById('strategy'),
        analysisRoleSelect: document.getElementById('analysis-role'),
        analyzeBtn: document.getElementById('analyze-btn'),
        suggestBtn: document.getElementById('suggest-btn'),
        
        // Current Tasks
        taskCount: document.getElementById('task-count'),
        currentTasksList: document.getElementById('current-tasks-list'),
        clearTasksBtn: document.getElementById('clear-tasks-btn'),
        
        // Dependency Dropdown
        dependencyDropdownTrigger: document.getElementById('dependency-dropdown-trigger'),
        dependencyDropdownMenu: document.getElementById('dependency-dropdown-menu'),
        dependencyOptions: document.getElementById('dependency-options'),
        dependencySelectedDisplay: document.getElementById('dependency-selected-display'),
        selectedDependenciesList: document.getElementById('selected-dependencies-list'),
        dependencyCount: document.getElementById('dependency-count'),
        
        // Results
        loadingState: document.getElementById('loading-state'),
        errorState: document.getElementById('error-state'),
        errorMessage: document.getElementById('error-message'),
        resultsListView: document.getElementById('results-list-view'),
        resultsMatrixView: document.getElementById('results-matrix-view'),
        warningsSection: document.getElementById('warnings-section'),
        warningsList: document.getElementById('warnings-list'),
        circularDepsSection: document.getElementById('circular-deps-section'),
        circularDepsList: document.getElementById('circular-deps-list'),
        
        // View Toggle
        viewToggleButtons: document.querySelectorAll('.toggle-btn'),
    };
    console.log('Elements initialized:', Object.keys(elements).length, 'elements');
}

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    initializeElements();
    loadTasksFromDatabase();
    initializeTabs();
    initializeForms();
    initializeButtons();
    initializeViewToggle();
    initializeCustomWeights();
    initializeDependencyDropdown();
    initializeImportanceSlider();
    initializeNotesModal();
    updateUI();
});


// Notes Modal Management

function initializeNotesModal() {
    const modal = document.getElementById('notes-modal');
    const closeBtn = document.querySelector('.notes-modal-close');
    const closeButton = document.querySelector('.notes-modal-close-btn');
    
    if (!modal) return;
    
    // Close modal when clicking the X button
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // Close modal when clicking the Close button
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside the modal content
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
        }
    });
}

function showNotesModal(task) {
    const modal = document.getElementById('notes-modal');
    const modalBody = document.getElementById('notes-modal-text');
    const modalTitle = document.getElementById('notes-modal-title');
    
    if (!modal || !modalBody) return;
    
    // Update title with task name
    if (modalTitle && task.title) {
        modalTitle.textContent = `Notes: ${task.title}`;
    }
    
    if (task.notes && task.notes.trim() !== '') {
        modalBody.innerHTML = escapeHtml(task.notes).replace(/\n/g, '<br>');
        modal.style.display = 'block';
    } else {
        modalBody.innerHTML = '<em style="color: #999;">No notes available for this task.</em>';
        modal.style.display = 'block';
    }
}


// Tab Management


function initializeTabs() {
    elements.tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update button states
    elements.tabButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content (only single and bulk tabs now)
    elements.singleTab.classList.toggle('active', tabName === 'single');
    elements.bulkTab.classList.toggle('active', tabName === 'bulk');
}


// Form Handling


function initializeForms() {
    // Single task form button
    const addTaskBtn = document.getElementById('add-task-btn');
    if (addTaskBtn) {
        addTaskBtn.addEventListener('click', handleSingleTaskSubmit);
        console.log('Add task button initialized');
    } else {
        console.error('Add task button not found!');
    }
    
    // Bulk JSON form button
    const loadTasksBtn = document.getElementById('load-tasks-btn');
    if (loadTasksBtn) {
        loadTasksBtn.addEventListener('click', handleBulkTaskSubmit);
        console.log('Load tasks button initialized');
    } else {
        console.error('Load tasks button not found!');
    }
}

function handleSingleTaskSubmit(e) {
    console.log('Add task button clicked');
    if (e) e.preventDefault();

    const form = document.getElementById('single-task-form');
    if (!form) {
        console.error('Form not found!');
        return;
    }
    
    const formData = new FormData(form);
    const selectedDependencies = getSelectedDependencies();

    // Get hours and minutes separately and convert to decimal hours
    const hours = parseInt(formData.get('estimated_hours') || '0');
    const minutes = parseInt(formData.get('estimated_minutes') || '0');
    const estimatedHours = hours + (minutes / 60);

    const task = {
        id: `task_${Date.now()}`,
        title: formData.get('title'),
        due_date: formData.get('due_date'),
        due_time: formData.get('due_time'),
        estimated_hours: estimatedHours,
        importance: parseInt(formData.get('importance')),
        dependencies: selectedDependencies,
        role: formData.get('role') || 'developer',
        notes: formData.get('notes') || '',
    };

    console.log('Task created:', task);

    // Validate required fields
    if (!task.title || !task.due_date || !task.due_time || isNaN(task.estimated_hours) || task.estimated_hours < 0.1) {
        showError('Please fill in all required fields with valid values. Estimated time must be at least 6 minutes.');
        return;
    }

    addTask(task).then(() => {
        alert('Task added successfully!');
        form.reset();
        clearDependencySelection();
    }).catch(error => {
        console.error('Failed to add task:', error);
    });

    // Reset importance slider display to default value (5)
    const importanceSlider = document.getElementById('importance');
    const importanceValue = document.getElementById('importance-value');
    if (importanceSlider && importanceValue) {
        importanceSlider.value = '5';
        importanceValue.textContent = '5';
        console.log('Importance slider reset to 5');
    }

    updateUI();
    console.log('Form submission complete');
}

async function handleBulkTaskSubmit(e) {
    console.log('Load tasks button clicked');
    if (e) e.preventDefault();
    
    const jsonText = document.getElementById('bulk-json').value.trim();
    
    if (!jsonText) {
        showError('Please enter JSON task data');
        return;
    }
    
    try {
        const tasksData = JSON.parse(jsonText);
        
        if (!Array.isArray(tasksData)) {
            showError('JSON must be an array of tasks');
            return;
        }
        
        // First pass: Save all tasks WITHOUT dependencies to get their database IDs
        console.log('📝 First pass: Saving tasks without dependencies...');
        const savedTasks = [];
        
        for (let i = 0; i < tasksData.length; i++) {
            const task = tasksData[i];
            const processedTask = {
                title: task.title,
                due_date: task.due_date,
                due_time: task.due_time || '23:59',
                estimated_hours: task.estimated_hours || 1.0,
                importance: task.importance || 5,
                dependencies: [], // Save without dependencies first
                role: task.role || 'developer',
                notes: task.notes || '',
            };
            
            const savedTask = await addTask(processedTask);
            savedTasks.push(savedTask);
            console.log(`Task ${i+1} saved with ID: ${savedTask.id}`);
        }
        
        // Create mapping: JSON array index (1-based) -> database ID
        const indexToIdMap = {};
        savedTasks.forEach((task, index) => {
            indexToIdMap[index + 1] = task.id; // Map 1-based index to database ID
        });
        
        console.log('Index to ID mapping:', indexToIdMap);
        
        // Second pass: Update tasks with corrected dependencies
        console.log('🔄 Second pass: Updating dependencies...');
        for (let i = 0; i < tasksData.length; i++) {
            const originalTask = tasksData[i];
            const savedTask = savedTasks[i];
            
            if (originalTask.dependencies && originalTask.dependencies.length > 0) {
                // Map JSON indices to actual database IDs
                const mappedDependencies = originalTask.dependencies.map(depIndex => {
                    const mappedId = indexToIdMap[depIndex];
                    console.log(`  Mapping dependency ${depIndex} -> ${mappedId}`);
                    return mappedId;
                }).filter(id => id !== undefined);
                
                // Update the task with correct dependencies
                savedTask.dependencies = mappedDependencies;
                await updateTaskInDatabase(savedTask);
                console.log(`Task "${savedTask.title}" dependencies updated:`, mappedDependencies);
            }
        }
        
        // Reload tasks from database to get complete data with IDs and notes
        await loadTasksFromDatabase();
        
        console.log('✅ All tasks loaded with corrected dependencies');
        switchTab('single'); // Switch back to single tab after loading
    } catch (error) {
        showError(`Invalid JSON: ${error.message}`);
    }
}

// Task Management

async function addTask(task) {
    try {
        // Don't send id if it's a temporary one
        const taskData = { ...task };
        if (taskData.id && taskData.id.startsWith('task_')) {
            delete taskData.id; // Let database generate the ID
        }
        
        const savedTask = await saveTaskToDatabase(taskData);
        tasks.push(savedTask);
        updateDependencyDropdown();
        updateUI();
        return savedTask;
    } catch (error) {
        showError(`Failed to add task: ${error.message}`);
        throw error;
    }
}

async function removeTask(taskId) {
    try {
        await deleteTaskFromDatabase(taskId);
        tasks = tasks.filter(t => t.id != taskId); // Use != for loose comparison
        // Remove from dependencies of other tasks
        tasks.forEach(task => {
            task.dependencies = task.dependencies.filter(dep => dep != taskId);
        });
        // Remove from selected dependencies if present
        selectedDependencyIds = selectedDependencyIds.filter(id => id != taskId);
        updateDependencyDropdown();
        updateDependencyDisplay();
        updateUI();
    } catch (error) {
        showError(`Failed to remove task: ${error.message}`);
    }
}

async function clearAllTasks() {
    if (confirm('Are you sure you want to clear all tasks?')) {
        try {
            // Delete all tasks from database
            const deletePromises = tasks.map(task => deleteTaskFromDatabase(task.id));
            await Promise.all(deletePromises);
            
            tasks = [];
            currentResults = null;
            selectedDependencyIds = [];
            updateDependencyDropdown();
            updateDependencyDisplay();
            updateUI();
            clearResults();
        } catch (error) {
            showError(`Failed to clear tasks: ${error.message}`);
        }
    }
}


// Database API Functions


async function loadTasksFromDatabase() {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/`);
        
        if (!response.ok) {
            throw new Error('Failed to load tasks from database');
        }
        
        const data = await response.json();
        tasks = data;
        updateDependencyDropdown();
        updateUI();
    } catch (error) {
        console.error('Failed to load tasks from database:', error);
        showError('Failed to load tasks from database');
        tasks = [];
    }
}

async function saveTaskToDatabase(task) {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(task),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to save task');
        }
        
        const savedTask = await response.json();
        return savedTask;
    } catch (error) {
        console.error('Failed to save task to database:', error);
        throw error;
    }
}

async function deleteTaskFromDatabase(taskId) {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/`, {
            method: 'DELETE',
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete task');
        }
    } catch (error) {
        console.error('Failed to delete task from database:', error);
        throw error;
    }
}

async function updateTaskInDatabase(task) {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${task.id}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(task),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to update task');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Failed to update task in database:', error);
        throw error;
    }
}

// Importance Slider Management


function initializeImportanceSlider() {
    const importanceSlider = document.getElementById('importance');
    const importanceValue = document.getElementById('importance-value');

    if (importanceSlider && importanceValue) {
        // Update display value on slider change
        importanceSlider.addEventListener('input', () => {
            importanceValue.textContent = importanceSlider.value;
            console.log('Importance slider value:', importanceSlider.value);
        });

        // Set initial value
        importanceValue.textContent = importanceSlider.value;
        console.log('Importance slider initialized with value:', importanceSlider.value);
    } else {
        console.error('Importance slider elements not found!', {
            slider: !!importanceSlider,
            value: !!importanceValue
        });
    }
}


// Dependency Dropdown Management


let selectedDependencyIds = [];

function initializeDependencyDropdown() {
    if (!elements.dependencyDropdownTrigger) {
        console.error('Dependency dropdown trigger not found!');
        return;
    }
    
    console.log('Dependency dropdown initialized');
    
    // Toggle dropdown on trigger click
    elements.dependencyDropdownTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        console.log('Dependency dropdown trigger clicked');
        toggleDependencyDropdown();
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (elements.dependencyDropdownMenu && elements.dependencyDropdownTrigger) {
            if (!elements.dependencyDropdownMenu.contains(e.target) && 
                !elements.dependencyDropdownTrigger.contains(e.target)) {
                closeDependencyDropdown();
            }
        }
    });
    
    // Prevent dropdown from closing when clicking inside
    if (elements.dependencyDropdownMenu) {
        elements.dependencyDropdownMenu.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    updateDependencyDropdown();
}

function toggleDependencyDropdown() {
    const menu = elements.dependencyDropdownMenu;
    if (!menu) return;
    
    const isOpen = menu.style.display !== 'none';
    menu.style.display = isOpen ? 'none' : 'block';
    
    if (!isOpen) {
        if (elements.dependencyDropdownTrigger) {
            elements.dependencyDropdownTrigger.classList.add('open');
        }
    } else {
        if (elements.dependencyDropdownTrigger) {
            elements.dependencyDropdownTrigger.classList.remove('open');
        }
    }
}

function closeDependencyDropdown() {
    const menu = elements.dependencyDropdownMenu;
    if (menu) {
        menu.style.display = 'none';
    }
    if (elements.dependencyDropdownTrigger) {
        elements.dependencyDropdownTrigger.classList.remove('open');
    }
}

function updateDependencyDropdown() {
    const optionsContainer = elements.dependencyOptions;
    if (!optionsContainer) return;
    
    // Get current task being edited (if any) - for now, exclude all tasks
    // In a real scenario, you'd exclude the current task being edited
    const availableTasks = tasks.filter(t => t.id && t.title);
    
    if (availableTasks.length === 0) {
        optionsContainer.innerHTML = '<div class="dependency-empty">No other tasks available</div>';
        return;
    }
    
    optionsContainer.innerHTML = availableTasks.map(task => {
        const isSelected = selectedDependencyIds.includes(task.id);
        return `
            <label class="dependency-option">
                <input type="checkbox"
                       value="${escapeHtml(task.id)}"
                       data-task-title="${escapeHtml(task.title)}"
                       ${isSelected ? 'checked' : ''}
                       class="dependency-checkbox">
                <span class="dependency-option-text">${escapeHtml(task.title || task.id)}</span>
            </label>
        `;
    }).join('');
    
    // Add event listeners to checkboxes
    optionsContainer.querySelectorAll('.dependency-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', handleDependencyCheckboxChange);
    });
}

function handleDependencyCheckboxChange(e) {
    const taskId = e.target.value;
    const isChecked = e.target.checked;
    
    if (isChecked) {
        if (!selectedDependencyIds.includes(taskId)) {
            selectedDependencyIds.push(taskId);
        }
    } else {
        selectedDependencyIds = selectedDependencyIds.filter(id => id !== taskId);
    }
    
    updateDependencyDisplay();
}

function updateDependencyDisplay() {
    const count = selectedDependencyIds.length;
    const countEl = elements.dependencyCount;
    const displayEl = elements.dependencySelectedDisplay;
    const listEl = elements.selectedDependenciesList;
    const triggerText = elements.dependencyDropdownTrigger?.querySelector('.dependency-trigger-text');
    
    if (count === 0) {
        if (countEl) countEl.style.display = 'none';
        if (displayEl) displayEl.style.display = 'none';
        if (triggerText) triggerText.textContent = 'Select Dependencies';
    } else {
        if (countEl) {
            countEl.textContent = `${count} selected`;
            countEl.style.display = 'inline';
        }
        if (triggerText) triggerText.textContent = 'Dependencies';
        if (displayEl) displayEl.style.display = 'block';
        
        if (listEl) {
            listEl.innerHTML = selectedDependencyIds.map(taskId => {
                // Use loose comparison to handle both string and integer IDs
                const task = tasks.find(t => t.id == taskId);
                const title = task ? task.title : taskId;
                return `
                    <div class="selected-dependency-item">
                        <span>${escapeHtml(title)}</span>
                        <button type="button" class="btn-remove-dependency" data-task-id="${escapeHtml(taskId)}">✕</button>
                    </div>
                `;
            }).join('');
            
            // Add remove button handlers
            listEl.querySelectorAll('.btn-remove-dependency').forEach(btn => {
                btn.addEventListener('click', () => {
                    const taskId = btn.dataset.taskId;
                    selectedDependencyIds = selectedDependencyIds.filter(id => id !== taskId);
                    updateDependencyDropdown();
                    updateDependencyDisplay();
                });
            });
        }
    }
}

function getSelectedDependencies() {
    return [...selectedDependencyIds];
}

function clearDependencySelection() {
    selectedDependencyIds = [];
    updateDependencyDisplay();
    updateDependencyDropdown();
}

function initializeButtons() {
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    elements.suggestBtn.addEventListener('click', handleSuggest);
    elements.clearTasksBtn.addEventListener('click', clearAllTasks);
    
    // Update analyze button state when strategy changes
    elements.strategySelect.addEventListener('change', () => {
        updateAnalyzeButtonState();
    });
}

function updateAnalyzeButtonState() {
    elements.analyzeBtn.disabled = tasks.length === 0;
}

function handleAnalyze() {
    if (tasks.length === 0) {
        showError('Please add at least one task before analyzing');
        return;
    }
    
    const strategy = elements.strategySelect.value;
    const role = elements.strategySelect.value === 'smart_balance' 
        ? elements.analysisRoleSelect.value 
        : null;
    
    // Get custom weights if enabled and strategy is smart_balance
    let customWeights = null;
    if (strategy === 'smart_balance') {
        const customWeightsCheckbox = document.getElementById('custom-weights-checkbox');
        if (customWeightsCheckbox && customWeightsCheckbox.checked) {
            customWeights = getCustomWeights();
            if (!customWeights) {
                // Validation failed, error already shown
                return;
            }
        }
    }
    
    analyzeTasks(strategy, role, customWeights);
}

function handleSuggest() {
    if (tasks.length === 0) {
        showError('Please add at least one task before getting suggestions');
        return;
    }
    
    const strategy = elements.strategySelect.value;
    const role = elements.strategySelect.value === 'smart_balance' 
        ? elements.analysisRoleSelect.value 
        : null;
    
    // Get custom weights if enabled and strategy is smart_balance
    let customWeights = null;
    if (strategy === 'smart_balance') {
        const customWeightsCheckbox = document.getElementById('custom-weights-checkbox');
        if (customWeightsCheckbox && customWeightsCheckbox.checked) {
            customWeights = getCustomWeights();
            if (!customWeights) {
                // Validation failed, error already shown
                return;
            }
        }
    }
    
    getSuggestions(strategy, role, customWeights);
}

// API Calls


async function analyzeTasks(strategy, role, customWeights = null) {
    showLoading();
    hideError();
    
    try {
        console.log('=== ANALYZE DEBUG ===');
        console.log('Total tasks:', tasks.length);
        console.log('First task:', JSON.stringify(tasks[0], null, 2));
        console.log('====================');
        
        // Check for circular dependencies BEFORE sending to backend
        console.log('Checking for circular dependencies...');
        const circularCheck = detectCircularDependenciesClient(tasks);
        console.log('Circular check result:', circularCheck);
        console.log('Has cycles?', circularCheck.hasCycles);
        console.log('Cycles found:', circularCheck.cycles);
        
        if (circularCheck.hasCycles) {
            console.log('🚨 CIRCULAR DEPENDENCIES DETECTED! Showing modal...');
            hideLoading();
            showCircularDependencyModal(circularCheck);
            return; // Prevent analysis
        }
        
        console.log('✅ No circular dependencies found. Proceeding with analysis...');
        
        const requestBody = {
            tasks: tasks,
            strategy: strategy,
        };
        
        if (role) {
            requestBody.role = role;
        }
        
        if (customWeights) {
            requestBody.custom_weights = customWeights;
        }
        
        const response = await fetch(`${API_BASE_URL}/tasks/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Analyze API error:', errorData);
            console.error('Validation details:', JSON.stringify(errorData.details, null, 2));
            console.error('Request body was:', JSON.stringify(requestBody, null, 2));
            
            // Show detailed error message
            let errorMsg = errorData.error || 'Analysis failed';
            if (errorData.details) {
                errorMsg += ': ' + JSON.stringify(errorData.details);
            }
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        currentResults = data;
        displayResults(data);
        
        // Automatically fetch suggestions after analysis
        await fetchSuggestionsAfterAnalysis(strategy, role, customWeights);
        
    } catch (error) {
        showError(error.message || 'Failed to analyze tasks. Make sure the backend server is running.');
    } finally {
        hideLoading();
    }
}

async function fetchSuggestionsAfterAnalysis(strategy, role, customWeights = null) {
    // Automatically fetch and display suggestions after analysis
    try {
        const requestBody = {
            tasks: tasks,
            strategy: strategy,
        };
        
        if (role) {
            requestBody.role = role;
        }
        
        if (customWeights) {
            requestBody.custom_weights = customWeights;
        }
        
        const response = await fetch(`${API_BASE_URL}/tasks/suggest/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });
        
        if (response.ok) {
            const data = await response.json();
            displaySuggestions(data.suggestions || []);
        }
    } catch (error) {
        // Silently fail - suggestions are optional
        console.error('Failed to fetch suggestions:', error);
    }
}

async function getSuggestions(strategy, role, customWeights = null) {
    showLoading();
    hideError();
    
    try {
        const requestBody = {
            tasks: tasks,
            strategy: strategy,
        };
        
        if (role) {
            requestBody.role = role;
        }
        
        if (customWeights) {
            requestBody.custom_weights = customWeights;
        }
        
        const response = await fetch(`${API_BASE_URL}/tasks/suggest/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || errorData.message || 'Failed to get suggestions');
        }
        
        const data = await response.json();
        // Display suggestions
        displaySuggestions(data.suggestions || []);
        
        // Also display full results if available
        if (data.suggestions && data.suggestions.length > 0) {
            // Get full task list from current results if available
            if (currentResults && currentResults.tasks) {
                displayTaskList(currentResults.tasks, currentResults.affected_task_ids || []);
            }
        }
        
    } catch (error) {
        showError(error.message || 'Failed to get suggestions. Make sure the backend server is running.');
    } finally {
        hideLoading();
    }
}


// Results Display


function displayResults(data) {
    displayTaskList(data.tasks, data.affected_task_ids || []);
    displayWarnings(data.warnings || []);
    displayCircularDependencies(data.circular_dependencies || [], data.circular_warning);
}

// Store suggested task IDs for highlighting
let suggestedTaskIds = [];

function displayTaskList(tasks, affectedTaskIds = []) {
    const container = elements.resultsListView;
    
    if (tasks.length === 0) {
        container.innerHTML = `
            <div class="empty-results">
                <div class="empty-icon">📊</div>
                <h3>No tasks to display</h3>
                <p>Add tasks and analyze to see results.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = tasks.map(task => {
        const isAffected = affectedTaskIds.includes(task.id);
        const isSuggested = suggestedTaskIds.includes(task.id);
        return createTaskCard(task, isAffected, isSuggested);
    }).join('');
    
    // Attach event listeners for show/hide details buttons
    attachTaskCardDetailsListeners();
}

function attachTaskCardDetailsListeners() {
    document.querySelectorAll('.btn-show-details').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent triggering parent card click
            const taskId = this.dataset.taskId;
            const detailsSection = document.getElementById(`details-${taskId}`);
            const detailsText = this.querySelector('.details-text');
            const detailsIcon = this.querySelector('.details-icon');
            
            if (!detailsSection) return;
            
            const isExpanded = detailsSection.style.display !== 'none';
            
            if (isExpanded) {
                // Collapse
                detailsSection.style.display = 'none';
                detailsText.textContent = 'Show Details';
                detailsIcon.textContent = '▼';
                this.classList.remove('expanded');
            } else {
                // Expand
                detailsSection.style.display = 'block';
                detailsText.textContent = 'Hide Details';
                detailsIcon.textContent = '▲';
                this.classList.add('expanded');
            }
        });
    });
    
    // Add click handlers to Notes buttons
    document.querySelectorAll('.btn-show-notes').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent triggering parent card click
            const notes = this.dataset.taskNotes || '';
            showNotesModal({ notes: notes });
        });
    });
}

function createTaskCard(task, isCircularAffected = false, isSuggested = false) {
    const taskId = task.id || `task-${Date.now()}-${Math.random()}`;
    const priorityClass = getPriorityClass(task.priority_label);
    const circularClass = isCircularAffected ? 'circular-warning' : '';
    const suggestedClass = isSuggested ? 'suggested-task' : '';
    const overdueBadge = task.is_overdue 
        ? '<span class="task-card-overdue">Overdue</span>' 
        : '';
    const circularBadge = isCircularAffected 
        ? '<span class="task-card-circular-badge">⚠ Circular Dependency</span>' 
        : '';
    const suggestedBadge = isSuggested 
        ? '<span class="task-card-suggested-badge">⭐ Today\'s Focus</span>' 
        : '';
    
    // Get component scores
    const componentScores = task.component_scores || {};
    const urgencyScore = componentScores.urgency || 0;
    const importanceScore = componentScores.importance || 0;
    const effortScore = componentScores.effort || 0;
    const dependencyScore = componentScores.dependency || 0;
    
    // Get dependent task titles
    const dependentTasks = getDependentTaskTitles(task.id, currentResults?.tasks || []);
    
    // Create progress bars
    const urgencyBar = createProgressBar(urgencyScore, 'urgency');
    const importanceBar = createProgressBar(importanceScore, 'importance');
    const effortBar = createProgressBar(effortScore, 'effort');
    const dependencyBar = createProgressBar(dependencyScore, 'dependency');
    
    const detailSection = `
        <div class="task-card-details" id="details-${taskId}" style="display: none;">
            <div class="details-section">
                <h4>Score Breakdown:</h4>
                <div class="score-bars">
                    <div class="score-bar-item">
                        <div class="score-bar-label">
                            <span>Urgency</span>
                            <span class="score-value">${urgencyScore.toFixed(1)}/100</span>
                        </div>
                        ${urgencyBar}
                    </div>
                    <div class="score-bar-item">
                        <div class="score-bar-label">
                            <span>Importance</span>
                            <span class="score-value">${importanceScore.toFixed(1)}/100</span>
                        </div>
                        ${importanceBar}
                    </div>
                    <div class="score-bar-item">
                        <div class="score-bar-label">
                            <span>Effort</span>
                            <span class="score-value">${effortScore.toFixed(1)}/100</span>
                        </div>
                        ${effortBar}
                    </div>
                    <div class="score-bar-item">
                        <div class="score-bar-label">
                            <span>Dependencies</span>
                            <span class="score-value">${dependencyScore.toFixed(1)}/100</span>
                        </div>
                        ${dependencyBar}
                    </div>
                </div>
            </div>
            ${dependentTasks.length > 0 ? `
                <div class="details-section">
                    <h4>Blocks these tasks:</h4>
                    <ul class="dependent-tasks-list">
                        ${dependentTasks.map(dep => `<li>→ ${escapeHtml(dep)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            <div class="details-section">
                <div class="task-role-info">
                    <strong>Role:</strong> ${escapeHtml(task.role || 'developer')}
                </div>
            </div>
            ${task.notes ? `
                <div class="details-section">
                    <h4>Notes:</h4>
                    <div class="task-notes-display">${escapeHtml(task.notes).replace(/\n/g, '<br>')}</div>
                </div>
            ` : ''}
        </div>
    `;
    
    return `
        <div class="task-card ${priorityClass} ${circularClass} ${suggestedClass}" data-task-id="${taskId}" data-task-notes="${escapeHtml(task.notes || '')}" style="cursor: pointer;" title="Click to view notes">
            ${suggestedBadge}
            ${circularBadge}
            <div class="task-card-header">
                <div>
                    <h3 class="task-card-title">${escapeHtml(task.title)}</h3>
                    ${overdueBadge}
                </div>
                <div>
                    <span class="task-card-priority ${task.priority_label.toLowerCase()}">${task.priority_label}</span>
                    <div class="task-card-score">${task.priority_score.toFixed(1)}</div>
                </div>
            </div>
            <div class="task-card-meta">
                <div class="task-card-meta-item">
                    <span>📅</span>
                    <span>${task.due_date} ${task.due_time}</span>
                </div>
                <div class="task-card-meta-item">
                    <span>⏱️</span>
                    <span>${formatEstimatedTime(task.estimated_hours)}</span>
                </div>
                <div class="task-card-meta-item">
                    <span>⭐</span>
                    <span>${task.importance}/10</span>
                </div>
                ${task.dependencies && task.dependencies.length > 0 
                    ? `<div class="task-card-meta-item">
                        <span>🔗</span>
                        <span>${task.dependencies.length} dependency(ies)</span>
                    </div>`
                    : ''}
            </div>
            <div class="task-card-actions">
                <button class="btn-show-details" data-task-id="${taskId}">
                    <span class="details-text">Show Details</span>
                    <span class="details-icon">▼</span>
                </button>
                <button class="btn-show-notes" data-task-id="${taskId}" data-task-notes="${escapeHtml(task.notes || '')}" title="View Notes">
                    📝 Notes
                </button>
            </div>
            ${detailSection}
        </div>
    `;
}

function createProgressBar(score, type) {
    const percentage = Math.min(100, Math.max(0, score));
    let colorClass = 'score-low';
    if (percentage >= 67) {
        colorClass = 'score-high';
    } else if (percentage >= 34) {
        colorClass = 'score-medium';
    }
    
    return `
        <div class="progress-bar-container">
            <div class="progress-bar ${colorClass}" style="width: ${percentage}%"></div>
        </div>
    `;
}

function getDependentTaskTitles(taskId, allTasks) {
    if (!taskId || !allTasks) return [];
    
    const dependentTitles = [];
    for (const otherTask of allTasks) {
        const dependencies = otherTask.dependencies || [];
        if (Array.isArray(dependencies) && dependencies.includes(taskId)) {
            dependentTitles.push(otherTask.title || otherTask.id);
        }
    }
    return dependentTitles;
}

function getPriorityClass(priorityLabel) {
    const label = priorityLabel.toLowerCase();
    if (label === 'high') return 'priority-high';
    if (label === 'medium') return 'priority-medium';
    if (label === 'low') return 'priority-low';
    return '';
}

function displayWarnings(warnings) {
    if (warnings.length === 0) {
        elements.warningsSection.style.display = 'none';
        return;
    }
    
    elements.warningsSection.style.display = 'block';
    elements.warningsList.innerHTML = warnings.map(warning => 
        `<li>${escapeHtml(warning)}</li>`
    ).join('');
}

function displayCircularDependencies(circularDeps, circularWarning = null) {
    const banner = document.getElementById('circular-warning-banner');
    const messageEl = document.getElementById('circular-warning-message');
    const chainsList = document.getElementById('circular-chains-list');
    const dismissBtn = document.getElementById('dismiss-warning-btn');
    
    if (!circularDeps || circularDeps.length === 0) {
        if (banner) banner.style.display = 'none';
        elements.circularDepsSection.style.display = 'none';
        return;
    }
    
    // Show warning banner
    if (banner) {
        banner.style.display = 'block';
        
        // Set warning message
        if (messageEl && circularWarning) {
            messageEl.textContent = circularWarning;
        } else if (messageEl) {
            messageEl.textContent = `${circularDeps.length} circular dependency chain(s) detected.`;
        }
        
        // Display chains
        if (chainsList) {
            chainsList.innerHTML = circularDeps.map(chain => 
                `<li>${escapeHtml(chain)}</li>`
            ).join('');
        }
        
        // Dismiss button handler
        if (dismissBtn) {
            dismissBtn.onclick = () => {
                banner.style.display = 'none';
            };
        }
    }
    
    // Also show in the circular deps section (existing functionality)
    elements.circularDepsSection.style.display = 'block';
    elements.circularDepsList.innerHTML = circularDeps.map(dep => 
        `<li>${escapeHtml(dep)}</li>`
    ).join('');
}

function clearResults() {
    elements.resultsListView.innerHTML = `
        <div class="empty-results">
            <div class="empty-icon">📊</div>
            <h3>No analysis yet</h3>
            <p>Add tasks and click "Analyze Tasks" to see prioritized results.</p>
        </div>
    `;
    elements.warningsSection.style.display = 'none';
    elements.circularDepsSection.style.display = 'none';
    
    // Hide suggestions section
    const focusSection = document.getElementById('todays-focus-section');
    if (focusSection) {
        focusSection.style.display = 'none';
    }
    suggestedTaskIds = [];
}

function displaySuggestions(suggestions) {
    const focusSection = document.getElementById('todays-focus-section');
    const container = document.getElementById('suggestions-container');
    
    if (!focusSection || !container) return;
    
    if (!suggestions || suggestions.length === 0) {
        focusSection.style.display = 'none';
        suggestedTaskIds = [];
        return;
    }
    
    // Store suggested task IDs for highlighting
    suggestedTaskIds = suggestions.map(s => s.id);
    
    // Show section
    focusSection.style.display = 'block';
    
    // Render suggestion cards
    container.innerHTML = suggestions.map((suggestion, index) => {
        const rank = index + 1;
        const rankEmoji = ['🥇', '🥈', '🥉'][index] || `${rank}.`;
        
        return `
            <div class="suggestion-card" data-task-id="${suggestion.id}">
                <div class="suggestion-header">
                    <div class="suggestion-rank">
                        <span class="rank-emoji">${rankEmoji}</span>
                        <div class="suggestion-info">
                            <h3 class="suggestion-title">${escapeHtml(suggestion.title)}</h3>
                            <div class="suggestion-score">Priority Score: ${suggestion.priority_score.toFixed(1)}</div>
                        </div>
                    </div>
                    <button class="btn-explanation" data-suggestion-index="${index}">
                        <span class="explanation-text">Why?</span>
                        <span class="explanation-icon">▼</span>
                    </button>
                </div>
                <div class="suggestion-explanation" id="explanation-${index}" style="display: none;">
                    <p>${escapeHtml(suggestion.explanation || 'No explanation available.')}</p>
                </div>
            </div>
        `;
    }).join('');
    
    // Add click handlers for expand/collapse
    document.querySelectorAll('.btn-explanation').forEach(btn => {
        btn.addEventListener('click', function() {
            const index = this.dataset.suggestionIndex;
            const explanation = document.getElementById(`explanation-${index}`);
            const icon = this.querySelector('.explanation-icon');
            
            if (explanation.style.display === 'none') {
                explanation.style.display = 'block';
                icon.textContent = '▲';
                this.classList.add('expanded');
            } else {
                explanation.style.display = 'none';
                icon.textContent = '▼';
                this.classList.remove('expanded');
            }
        });
    });
    
    // Re-render task list to highlight suggested tasks
    if (currentResults && currentResults.tasks) {
        displayTaskList(currentResults.tasks, currentResults.affected_task_ids || []);
    }
}

// Eisenhower Matrix


function initializeViewToggle() {
    elements.viewToggleButtons.forEach(button => {
        button.addEventListener('click', () => {
            const view = button.dataset.view;
            switchView(view);
        });
    });
}

function switchView(view) {
    // Update button states
    elements.viewToggleButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
    
    // Update view visibility
    elements.resultsListView.style.display = view === 'list' ? 'block' : 'none';
    elements.resultsMatrixView.style.display = view === 'matrix' ? 'block' : 'none';
    
    // Render matrix if switching to matrix view
    if (view === 'matrix' && currentResults) {
        renderEisenhowerMatrix(currentResults.tasks);
    }
}

function renderEisenhowerMatrix(tasks) {
    if (!tasks || tasks.length === 0) {
        clearMatrix();
        return;
    }
    
    // Calculate urgency and importance thresholds
    const urgencyScores = tasks.map(t => t.component_scores?.urgency || 0);
    const importanceScores = tasks.map(t => t.component_scores?.importance || 0);
    
    const urgencyThreshold = urgencyScores.reduce((a, b) => a + b, 0) / urgencyScores.length;
    const importanceThreshold = importanceScores.reduce((a, b) => a + b, 0) / importanceScores.length;
    
    // Store thresholds for display
    window.matrixThresholds = {
        urgency: urgencyThreshold,
        importance: importanceThreshold
    };
    
    // Display threshold info
    const matrixInfo = document.getElementById('matrix-info');
    const urgencyThresholdEl = document.getElementById('urgency-threshold');
    const importanceThresholdEl = document.getElementById('importance-threshold');
    
    if (matrixInfo && urgencyThresholdEl && importanceThresholdEl) {
        urgencyThresholdEl.textContent = urgencyThreshold.toFixed(1);
        importanceThresholdEl.textContent = importanceThreshold.toFixed(1);
        matrixInfo.style.display = 'block';
    }
    
    // Categorize tasks into quadrants
    const quadrants = {
        'important-urgent': [],
        'important-not-urgent': [],
        'not-important-urgent': [],
        'not-important-not-urgent': [],
    };
    
    tasks.forEach(task => {
        const urgency = task.component_scores?.urgency || 0;
        const importance = task.component_scores?.importance || 0;
        
        const isUrgent = urgency >= urgencyThreshold;
        const isImportant = importance >= importanceThreshold;
        
        if (isImportant && isUrgent) {
            quadrants['important-urgent'].push(task);
        } else if (isImportant && !isUrgent) {
            quadrants['important-not-urgent'].push(task);
        } else if (!isImportant && isUrgent) {
            quadrants['not-important-urgent'].push(task);
        } else {
            quadrants['not-important-not-urgent'].push(task);
        }
    });
    
    // Render each quadrant with enhanced task cards
    Object.keys(quadrants).forEach(quadrantKey => {
        const quadrantId = `quadrant-${quadrantKey}`;
        const quadrantElement = document.getElementById(quadrantId);
        if (quadrantElement) {
            const tasksContainer = quadrantElement.querySelector('.quadrant-tasks');
            const taskCount = quadrants[quadrantKey].length;
            
            // Update quadrant header with count
            const header = quadrantElement.querySelector('h4');
            if (header) {
                header.innerHTML = `${header.textContent.split('(')[0].trim()} <span class="quadrant-count">(${taskCount})</span>`;
            }
            
            if (taskCount === 0) {
                tasksContainer.innerHTML = '<div class="matrix-empty">No tasks in this quadrant</div>';
            } else {
                tasksContainer.innerHTML = quadrants[quadrantKey].map((task, index) => 
                    createMatrixTaskCard(task, index)
                ).join('');
            }
        }
    });
    
    // Add event listeners for interactive elements
    attachMatrixInteractivity();
}

function createMatrixTaskCard(task, index) {
    const priorityClass = getPriorityClass(task.priority_label);
    const overdueBadge = task.is_overdue 
        ? '<span class="matrix-task-overdue">⚠ Overdue</span>' 
        : '';
    
    const urgency = task.component_scores?.urgency || 0;
    const importance = task.component_scores?.importance || 0;
    
    return `
        <div class="matrix-task-card ${priorityClass}" data-task-index="${index}" data-task-id="${task.id}" data-task-title="${escapeHtml(task.title)}" data-task-notes="${escapeHtml(task.notes || '')}" style="cursor: pointer;" title="Click to view notes">
            <div class="matrix-task-header">
                <div class="matrix-task-title">${escapeHtml(task.title)}</div>
                <div class="matrix-task-priority ${task.priority_label.toLowerCase()}">${task.priority_label}</div>
            </div>
            <div class="matrix-task-score">Score: ${task.priority_score.toFixed(1)}</div>
            ${overdueBadge}
            <div class="matrix-task-details">
                <div class="matrix-task-detail-item">
                    <span class="detail-label">Urgency:</span>
                    <span class="detail-value">${urgency.toFixed(1)}</span>
                </div>
                <div class="matrix-task-detail-item">
                    <span class="detail-label">Importance:</span>
                    <span class="detail-value">${importance.toFixed(1)}</span>
                </div>
                <div class="matrix-task-detail-item">
                    <span class="detail-label">Due:</span>
                    <span class="detail-value">${task.due_date} ${task.due_time}</span>
                </div>
                <div class="matrix-task-detail-item">
                    <span class="detail-label">Hours:</span>
                    <span class="detail-value">${formatEstimatedTime(task.estimated_hours)}</span>
                </div>
            </div>
            <div class="matrix-task-expand" style="display: none;">
                <div class="matrix-task-explanations">
                    <strong>Score Breakdown:</strong>
                    <ul>
                        ${task.explanations ? task.explanations.map(exp => 
                            `<li>${escapeHtml(exp)}</li>`
                        ).join('') : ''}
                    </ul>
                </div>
            </div>
        </div>
    `;
}

function attachMatrixInteractivity() {
    // Add click handlers to expand/collapse task details and show notes
    document.querySelectorAll('.matrix-task-card').forEach(card => {
        card.addEventListener('click', function(e) {
            // Don't toggle if clicking on a link or button
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                return;
            }
            
            // Get task ID and find full task data from currentResults
            const taskIndex = parseInt(this.dataset.taskIndex);
            const task = currentResults?.tasks[taskIndex];
            
            console.log('Matrix card clicked, index:', taskIndex);
            console.log('Task from currentResults:', task);
            console.log('Task notes:', task?.notes);
            
            if (task) {
                showNotesModal(task);
            } else {
                console.error('Task not found for index:', taskIndex);
            }
        });
        
        // Removed expand/collapse functionality in favor of notes modal
        
        // Add hover effect
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        card.addEventListener('mouseleave', function() {
            if (!this.classList.contains('expanded')) {
                this.style.transform = 'translateY(0)';
            }
        });
    });
}

function clearMatrix() {
    const quadrantIds = [
        'quadrant-important-urgent',
        'quadrant-important-not-urgent',
        'quadrant-not-important-urgent',
        'quadrant-not-important-not-urgent',
    ];
    
    quadrantIds.forEach(id => {
        const quadrant = document.getElementById(id);
        if (quadrant) {
            const tasksContainer = quadrant.querySelector('.quadrant-tasks');
            const header = quadrant.querySelector('h4');
            if (tasksContainer) {
                tasksContainer.innerHTML = '';
            }
            if (header) {
                // Reset header to original text
                const originalText = header.textContent.split('(')[0].trim();
                if (originalText.includes('Do First')) header.innerHTML = 'Do First <span class="quadrant-count">(0)</span>';
                else if (originalText.includes('Schedule')) header.innerHTML = 'Schedule <span class="quadrant-count">(0)</span>';
                else if (originalText.includes('Delegate')) header.innerHTML = 'Delegate <span class="quadrant-count">(0)</span>';
                else if (originalText.includes('Eliminate')) header.innerHTML = 'Eliminate <span class="quadrant-count">(0)</span>';
            }
        }
    });
}


function updateUI() {
    updateTaskCount();
    updateCurrentTasksList();
    updateAnalyzeButtonState();
}

function updateTaskCount() {
    elements.taskCount.textContent = tasks.length;
}

function updateCurrentTasksList() {
    const container = elements.currentTasksList;
    
    if (tasks.length === 0) {
        container.innerHTML = '<p class="empty-state">No tasks added yet. Add tasks using the form above.</p>';
        elements.clearTasksBtn.style.display = 'none';
        return;
    }
    
    elements.clearTasksBtn.style.display = 'block';
    
    container.innerHTML = tasks.map(task => `
        <div class="current-task-item">
            <div>
                <div class="current-task-item-title">${escapeHtml(task.title)}</div>
                <div class="current-task-item-meta">
                    ${task.due_date} ${task.due_time} • ${formatEstimatedTime(task.estimated_hours)} • ${task.importance}/10
                </div>
            </div>
            <div style="display: flex; gap: 8px;">
                <button class="btn btn-secondary btn-small" onclick="showNotesForTask('${task.id}')">Notes</button>
                <button class="btn btn-secondary btn-small" onclick="removeTaskById('${task.id}')">Remove</button>
            </div>
        </div>
    `).join('');
}


function formatEstimatedTime(hours) {
    // Format decimal hours to readable time format (e.g., 8.5 -> '8h 30m')
    const totalMinutes = Math.round(hours * 60);
    const displayHours = Math.floor(totalMinutes / 60);
    const displayMinutes = totalMinutes % 60;

    if (displayMinutes === 0) {
        return `${displayHours}h`;
    } else if (displayHours === 0) {
        return `${displayMinutes}m`;
    } else {
        return `${displayHours}h ${displayMinutes}m`;
    }
}

// Global function for remove button
window.removeTaskById = function(taskId) {
    // Convert to number if it's a string to match database IDs
    const numericId = typeof taskId === 'string' ? parseInt(taskId) : taskId;
    removeTask(numericId);
};

// Global function for notes button
window.showNotesForTask = function(taskId) {
    // Convert to number if it's a string to match database IDs
    const numericId = typeof taskId === 'string' ? parseInt(taskId) : taskId;
    const task = tasks.find(t => t.id == numericId); // Use == for loose comparison
    if (task) {
        showNotesModal(task);
    } else {
        console.error('Task not found:', taskId, 'Available tasks:', tasks.map(t => t.id));
    }
};



function initializeNotesModal() {
    const modal = document.getElementById('notes-modal');
    const closeBtns = document.querySelectorAll('.notes-modal-close, .notes-modal-close-btn');
    
    if (!modal) return;
    
    // Close modal when clicking close buttons
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    });
    
    // Close modal when clicking outside the modal content
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
        }
    });
}

function showNotesModal(task) {
    const modal = document.getElementById('notes-modal');
    const modalText = document.getElementById('notes-modal-text');
    const modalTitle = document.getElementById('notes-modal-title');
    
    if (!modal || !modalText) {
        console.error('Modal elements not found!');
        return;
    }
    
    if (modalTitle) {
        modalTitle.textContent = `Notes: ${task.title}`;
    }
    
    if (task.notes && task.notes.trim() !== '') {
        modalText.innerHTML = escapeHtml(task.notes).replace(/\n/g, '<br>');
    } else {
        modalText.innerHTML = '<em style="color: #999;">No notes available for this task.</em>';
    }
    
    modal.style.display = 'block';
}



function showLoading() {
    elements.loadingState.style.display = 'block';
    elements.resultsListView.style.display = 'none';
    elements.resultsMatrixView.style.display = 'none';
    elements.analyzeBtn.disabled = true;
    elements.suggestBtn.disabled = true;
}

function hideLoading() {
    elements.loadingState.style.display = 'none';
    elements.analyzeBtn.disabled = false;
    elements.suggestBtn.disabled = false;
}

function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorState.style.display = 'block';
    elements.resultsListView.style.display = 'none';
    elements.resultsMatrixView.style.display = 'none';
}

function hideError() {
    elements.errorState.style.display = 'none';
}



function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}



elements.strategySelect.addEventListener('change', () => {
    const strategy = elements.strategySelect.value;
    const roleSelectorGroup = document.getElementById('role-selector-group');
    
    // Show role selector only for smart_balance strategy
    if (strategy === 'smart_balance') {
        roleSelectorGroup.style.display = 'block';
    } else {
        roleSelectorGroup.style.display = 'none';
    }
    
    // Re-analyze if we have results
    if (currentResults && tasks.length > 0) {
        const role = strategy === 'smart_balance' 
            ? elements.analysisRoleSelect.value 
            : null;
        analyzeTasks(strategy, role);
    }
});




// Custom Weights Management


function initializeCustomWeights() {
    const strategySelect = elements.strategySelect;
    const customWeightsSection = document.getElementById('custom-weights-section');
    const customWeightsCheckbox = document.getElementById('custom-weights-checkbox');
    const weightsControls = document.getElementById('weights-controls');
    
    // Show/hide custom weights section based on strategy
    const updateCustomWeightsVisibility = () => {
        const strategy = strategySelect.value;
        if (strategy === 'smart_balance') {
            if (customWeightsSection) customWeightsSection.style.display = 'block';
        } else {
            if (customWeightsSection) customWeightsSection.style.display = 'none';
            if (customWeightsCheckbox) customWeightsCheckbox.checked = false;
            if (weightsControls) weightsControls.style.display = 'none';
        }
    };
    
    // Initial visibility
    updateCustomWeightsVisibility();
    
    // Update on strategy change
    strategySelect.addEventListener('change', updateCustomWeightsVisibility);
    
    // Toggle weights controls when checkbox is clicked
    if (customWeightsCheckbox) {
        customWeightsCheckbox.addEventListener('change', function() {
            if (weightsControls) {
                weightsControls.style.display = this.checked ? 'block' : 'none';
            }
            
            // Reset to default values if unchecked
            if (!this.checked) {
                resetWeightsToDefaults();
            }
            
            // Update total
            updateWeightsTotal();
        });
    }
    
    // Add listeners to all weight sliders
    const sliders = [
        { id: 'weight-urgency', valueId: 'weight-urgency-value' },
        { id: 'weight-importance', valueId: 'weight-importance-value' },
        { id: 'weight-effort', valueId: 'weight-effort-value' },
        { id: 'weight-dependencies', valueId: 'weight-dependencies-value' }
    ];
    
    sliders.forEach(({ id, valueId }) => {
        const slider = document.getElementById(id);
        const valueDisplay = document.getElementById(valueId);
        
        if (slider && valueDisplay) {
            slider.addEventListener('input', function() {
                valueDisplay.textContent = this.value;
                updateWeightsTotal();
            });
        }
    });
}

function updateWeightsTotal() {
    const urgency = parseInt(document.getElementById('weight-urgency')?.value || 0);
    const importance = parseInt(document.getElementById('weight-importance')?.value || 0);
    const effort = parseInt(document.getElementById('weight-effort')?.value || 0);
    const dependencies = parseInt(document.getElementById('weight-dependencies')?.value || 0);
    
    const total = urgency + importance + effort + dependencies;
    
    const totalDisplay = document.getElementById('weight-total-value');
    const errorDisplay = document.getElementById('weight-error');
    const analyzeBtn = elements.analyzeBtn;
    
    if (totalDisplay) {
        totalDisplay.textContent = total;
        
        // Color code the total
        if (total === 100) {
            totalDisplay.style.color = '#2ecc71'; // Green
            if (errorDisplay) errorDisplay.style.display = 'none';
            if (analyzeBtn && tasks.length > 0) analyzeBtn.disabled = false;
        } else {
            totalDisplay.style.color = '#e74c3c'; // Red
            if (errorDisplay) errorDisplay.style.display = 'block';
            if (analyzeBtn) analyzeBtn.disabled = true;
        }
    }
}

function resetWeightsToDefaults() {
    // Reset to Smart Balance Developer defaults
    const defaults = {
        'weight-urgency': 30,
        'weight-importance': 30,
        'weight-effort': 20,
        'weight-dependencies': 20
    };
    
    Object.keys(defaults).forEach(id => {
        const slider = document.getElementById(id);
        const valueDisplay = document.getElementById(`${id}-value`);
        
        if (slider) {
            slider.value = defaults[id];
            if (valueDisplay) {
                valueDisplay.textContent = defaults[id];
            }
        }
    });
    
    updateWeightsTotal();
}

function getCustomWeights() {
    const customWeightsCheckbox = document.getElementById('custom-weights-checkbox');
    
    // Only return custom weights if checkbox is checked
    if (!customWeightsCheckbox || !customWeightsCheckbox.checked) {
        return null;
    }
    
    const urgency = parseInt(document.getElementById('weight-urgency')?.value || 0);
    const importance = parseInt(document.getElementById('weight-importance')?.value || 0);
    const effort = parseInt(document.getElementById('weight-effort')?.value || 0);
    const dependencies = parseInt(document.getElementById('weight-dependencies')?.value || 0);
    
    const total = urgency + importance + effort + dependencies;
    
    // Validate total equals 100
    if (total !== 100) {
        showError(`Weights must sum to 100%. Current sum: ${total}%`);
        return null;
    }
    
    // Return weights as object with backend-expected keys
    return {
        urgency: urgency,
        importance: importance,
        effort: effort,
        dependencies: dependencies
    };
}

// Circular Dependency Detection (Client-side)
function detectCircularDependenciesClient(taskList) {
    const taskLookup = {};
    const graph = {};
    const taskIds = new Set();
    
    console.log('🔍 Building dependency graph...');
    
    // Build task lookup and forward graph (task -> its dependencies)
    taskList.forEach(task => {
        const taskId = task.id;
        taskIds.add(taskId);
        taskLookup[taskId] = task;
        
        // Initialize graph entry for this task
        if (!graph[taskId]) {
            graph[taskId] = [];
        }
        
        // Add forward edges: this task depends on these tasks
        const deps = task.dependencies || [];
        deps.forEach(depId => {
            // Only add if the dependency exists in our task list
            if (taskList.some(t => t.id == depId)) {
                graph[taskId].push(depId);
            }
        });
    });
    
    console.log('Graph:', graph);
    console.log('Task IDs:', Array.from(taskIds));
    
    const cycles = [];
    const affectedTaskIds = new Set();
    const visited = new Set();
    const recStack = new Set();
    const path = [];
    
    function dfs(node) {
        if (recStack.has(node)) {
            // Found a cycle!
            const cycleStart = path.indexOf(node);
            const cycle = [...path.slice(cycleStart), node];
            console.log('🔴 CYCLE FOUND:', cycle);
            cycles.push(cycle);
            cycle.forEach(id => affectedTaskIds.add(id));
            return true;
        }
        
        if (visited.has(node)) {
            return false;
        }
        
        visited.add(node);
        recStack.add(node);
        path.push(node);
        
        // Visit all dependencies of this node
        if (graph[node]) {
            for (const neighbor of graph[node]) {
                dfs(neighbor);
            }
        }
        
        recStack.delete(node);
        path.pop();
        return false;
    }
    
    // Check all tasks
    console.log('Starting DFS for all tasks...');
    taskIds.forEach(taskId => {
        if (!visited.has(taskId)) {
            console.log('Checking task:', taskId);
            dfs(taskId);
        }
    });
    
    console.log('Total cycles found:', cycles.length);
    
    return {
        hasCycles: cycles.length > 0,
        cycles: cycles,
        affectedTaskIds: Array.from(affectedTaskIds),
        taskLookup: taskLookup
    };
}

function showCircularDependencyModal(circularCheck) {
    const modal = document.getElementById('circular-dependency-modal');
    const cyclesList = document.getElementById('circular-cycles-list');
    const affectedTasksList = document.getElementById('affected-tasks-list');
    const closeBtn = document.getElementById('circular-modal-close');
    const closeBtn2 = document.getElementById('circular-modal-close-btn');
    
    // Format cycles with task titles
    const cycleStrings = circularCheck.cycles.map(cycle => {
        const titles = cycle.map(id => {
            const task = circularCheck.taskLookup[id];
            return task ? `"${task.title}" (ID: ${id})` : `ID: ${id}`;
        });
        return titles.join(' → ');
    });
    
    cyclesList.innerHTML = cycleStrings.map(cycle => 
        `<li style="margin-bottom: 10px; color: #721c24; font-weight: 500;">${cycle}</li>`
    ).join('');
    
    // Show affected tasks with option to edit
    const affectedTasksHTML = circularCheck.affectedTaskIds.map(taskId => {
        const task = circularCheck.taskLookup[taskId];
        if (!task) return '';
        
        const depNames = (task.dependencies || []).map(depId => {
            const depTask = circularCheck.taskLookup[depId];
            return depTask ? depTask.title : `ID: ${depId}`;
        }).join(', ');
        
        return `
            <div style="padding: 10px; margin-bottom: 8px; background: #f8f9fa; border-left: 3px solid #dc3545; border-radius: 3px;">
                <strong>${task.title}</strong> (ID: ${taskId})<br>
                <small style="color: #666;">Dependencies: ${depNames || 'None'}</small><br>
                <button class="btn btn-sm" onclick="editTaskDependencies(${taskId})" style="margin-top: 5px; font-size: 12px; padding: 4px 8px;">
                    Edit Dependencies
                </button>
            </div>
        `;
    }).join('');
    
    affectedTasksList.innerHTML = affectedTasksHTML;
    
    // Show modal
    modal.style.display = 'flex';
    
    // Close handlers
    const closeModal = () => {
        modal.style.display = 'none';
    };
    
    closeBtn.onclick = closeModal;
    closeBtn2.onclick = closeModal;
    modal.onclick = (e) => {
        if (e.target === modal) {
            closeModal();
        }
    };
}

function editTaskDependencies(taskId) {
    // Close circular modal first
    document.getElementById('circular-dependency-modal').style.display = 'none';
    
    // Find the task
    const task = tasks.find(t => t.id == taskId);
    if (!task) {
        showError('Task not found');
        return;
    }
    
    // Scroll to top and switch to single tab
    window.scrollTo({ top: 0, behavior: 'smooth' });
    switchTab('single');
    
    // Pre-fill the form with task data
    setTimeout(() => {
        document.getElementById('task-title').value = task.title || '';
        document.getElementById('due-date').value = task.due_date || '';
        document.getElementById('due-time').value = task.due_time || '';
        document.getElementById('estimated-hours').value = Math.floor(task.estimated_hours || 0);
        document.getElementById('estimated-minutes').value = Math.round(((task.estimated_hours || 0) % 1) * 60);
        document.getElementById('importance').value = task.importance || 5;
        document.getElementById('task-role').value = task.role || 'developer';
        document.getElementById('task-notes').value = task.notes || '';
        
        // Set dependencies (clear them or allow editing)
        selectedDependencyIds = [...(task.dependencies || [])];
        updateDependencyDisplay();
        
        // Show a message
        showError(`Editing task: "${task.title}". Remove problematic dependencies and save.`);
        
        // Remove the task from the list temporarily so user can re-add with fixed deps
        removeTask(taskId);
    }, 300);
}
