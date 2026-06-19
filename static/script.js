document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const sqlEditor = document.getElementById("sqlEditor");
    const btnExecute = document.getElementById("btnExecute");
    const btnReset = document.getElementById("btnReset");
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    const templateButtons = document.querySelectorAll(".btn-template");
    const schemaColumns = document.querySelectorAll(".column-item");
    
    // Output containers
    const metricsPanel = document.getElementById("metricsPanel");
    const valEstimatedCost = document.getElementById("valEstimatedCost");
    const valEstimatedRows = document.getElementById("valEstimatedRows");
    const valActualTime = document.getElementById("valActualTime");
    const valActualRows = document.getElementById("valActualRows");
    
    // Results Grid Elements
    const resultsPlaceholder = document.getElementById("resultsPlaceholder");
    const resultsContainer = document.getElementById("resultsContainer");
    const resultsTable = document.getElementById("resultsTable");
    
    // Physical Plan Elements
    const physicalPlaceholder = document.getElementById("physicalPlaceholder");
    const physicalContainer = document.getElementById("physicalContainer");
    const physicalTreeRenderA = document.getElementById("physicalTreeRenderA");
    const physicalTreeRenderB = document.getElementById("physicalTreeRenderB");
    const physicalTreeRenderC = document.getElementById("physicalTreeRenderC");
    
    // Logical Plan Elements
    const logicalPlaceholder = document.getElementById("logicalPlaceholder");
    const logicalContainer = document.getElementById("logicalContainer");
    const logicalTreeRender = document.getElementById("logicalTreeRender");
    const optimizedTreeRender = document.getElementById("optimizedTreeRender");

    // Parsed AST Elements
    const parsedPlaceholder = document.getElementById("parsedPlaceholder");
    const parsedContainer = document.getElementById("parsedContainer");
    const parsedTreeRender = document.getElementById("parsedTreeRender");
    
    // Optimizer Dashboard Elements
    const optimizerSection = document.getElementById("optimizerSection");
    const comparisonTableBody = document.querySelector("#comparisonTable tbody");
    const chartBarsList = document.getElementById("chartBarsList");
    const bestPlanName = document.getElementById("bestPlanName");
    const bestPlanCost = document.getElementById("bestPlanCost");
    const bestPlanJoin = document.getElementById("bestPlanJoin");
    const bestPlanScan = document.getElementById("bestPlanScan");
    const bestPlanWhy = document.getElementById("bestPlanWhy");
    
    // New tab panel elements
    const comparisonPlaceholder = document.getElementById("comparisonPlaceholder");
    const comparisonContainer = document.getElementById("comparisonContainer");
    const reductionPctVal = document.getElementById("reductionPctVal");
    const comparisonExplanations = document.getElementById("comparisonExplanations");
    const compLogicalBefore = document.getElementById("compLogicalBefore");
    const compLogicalAfter = document.getElementById("compLogicalAfter");
    const compCostBefore = document.getElementById("compCostBefore");
    const compCostAfter = document.getElementById("compCostAfter");
    
    const historyList = document.getElementById("historyList");
    
    const statsTotalRecords = document.getElementById("statsTotalRecords");
    const statsRowsStudent = document.getElementById("statsRowsStudent");
    const statsRowsDepartment = document.getElementById("statsRowsDepartment");
    const statsRowsTeacher = document.getElementById("statsRowsTeacher");
    const statsRowsCourse = document.getElementById("statsRowsCourse");

    // Error Toast Elements
    const errorToast = document.getElementById("errorToast");
    const toastMessage = document.getElementById("toastMessage");
    const btnToastClose = document.getElementById("btnToastClose");

    // Initialize with a default query
    sqlEditor.value = "SELECT Student.name, Department.name \nFROM Student \nJOIN Department ON Student.dept_id = Department.id \nWHERE Student.cgpa > 3.7";

    // 1. Tab Switching Logic
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            // Toggle active tab button
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            // Toggle active tab content
            tabContents.forEach(content => {
                if (content.id === targetTab) {
                    content.classList.add("active");
                } else {
                    content.classList.remove("active");
                }
            });

            if (targetTab === "tab-history") {
                renderHistory();
            } else if (targetTab === "tab-statistics") {
                loadStatistics();
            }
        });
    });

    // 2. Load Quick Templates
    templateButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            sqlEditor.value = btn.getAttribute("data-sql");
            sqlEditor.focus();
        });
    });

    // 3. Schema Explorer Click to Insert Column name
    schemaColumns.forEach(item => {
        item.addEventListener("click", () => {
            const table = item.getAttribute("data-table");
            const column = item.getAttribute("data-column");
            const insertText = `${table}.${column}`;
            
            // Insert at current cursor position in textarea
            const startPos = sqlEditor.selectionStart;
            const endPos = sqlEditor.selectionEnd;
            const text = sqlEditor.value;
            
            sqlEditor.value = text.substring(0, startPos) + insertText + text.substring(endPos, text.length);
            sqlEditor.focus();
            
            // Reposition cursor after the inserted text
            sqlEditor.selectionStart = sqlEditor.selectionEnd = startPos + insertText.length;
        });
    });

    // 4. Reset Button
    btnReset.addEventListener("click", () => {
        sqlEditor.value = "";
        hideAllOutput();
        sqlEditor.focus();
    });

    // 5. Toast Notification Close
    btnToastClose.addEventListener("click", hideToast);

    // 6. SQL execute action
    btnExecute.addEventListener("click", runQuery);

    // Keyboard shortcut Ctrl + Enter inside SQL editor
    sqlEditor.addEventListener("keydown", (e) => {
        if (e.ctrlKey && e.key === "Enter") {
            e.preventDefault();
            runQuery();
        }
    });

    function runQuery() {
        const queryText = sqlEditor.value.trim();
        if (!queryText) {
            showToast("Query is empty. Please enter a valid SQL query.");
            return;
        }

        // Set Loading state
        btnExecute.disabled = true;
        const originalBtnContent = btnExecute.innerHTML;
        btnExecute.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i><span>Analyzing...</span>`;
        hideToast();

        fetch("/api/execute", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query: queryText })
        })
        .then(response => response.json())
        .then(data => {
            btnExecute.disabled = false;
            btnExecute.innerHTML = originalBtnContent;

            if (data.success) {
                renderOutput(data);
            } else {
                showToast(data.error || "An unknown error occurred during query simulation.");
                hideAllOutput();
            }
        })
        .catch(err => {
            btnExecute.disabled = false;
            btnExecute.innerHTML = originalBtnContent;
            showToast("Server communication error. Make sure Flask is running.");
            hideAllOutput();
            console.error(err);
        });
    }

    function renderOutput(data) {
        // 1. Render Metrics Dashboard
        metricsPanel.classList.remove("hidden");
        valEstimatedCost.textContent = data.cost_estimation ? data.cost_estimation.total_cost : "N/A";
        valEstimatedRows.textContent = data.cost_estimation ? data.cost_estimation.estimated_rows.toLocaleString() : "N/A";
        valActualTime.textContent = `${data.execution_time_ms} ms`;
        valActualRows.textContent = data.execution_result ? data.execution_result.total_rows.toLocaleString() : "0";

        // 2. Render Results Grid
        resultsPlaceholder.classList.add("hidden");
        resultsContainer.classList.remove("hidden");
        
        const execResult = data.execution_result;
        if (execResult && execResult.columns && execResult.columns.length > 0) {
            // Render Headers
            let headersHtml = "<tr>";
            execResult.columns.forEach(col => {
                headersHtml += `<th>${col}</th>`;
            });
            headersHtml += "</tr>";
            resultsTable.querySelector("thead").innerHTML = headersHtml;

            // Render Rows (limited to 100 on backend)
            let rowsHtml = "";
            if (execResult.rows.length === 0) {
                rowsHtml = `<tr><td colspan="${execResult.columns.length}" style="text-align: center; color: var(--text-muted);">No records found.</td></tr>`;
            } else {
                execResult.rows.forEach(row => {
                    rowsHtml += "<tr>";
                    execResult.columns.forEach(col => {
                        rowsHtml += `<td>${row[col] !== null ? row[col] : "<em>NULL</em>"}</td>`;
                    });
                    rowsHtml += "</tr>";
                });
            }
            resultsTable.querySelector("tbody").innerHTML = rowsHtml;
        } else {
            resultsTable.querySelector("thead").innerHTML = "";
            resultsTable.querySelector("tbody").innerHTML = `<tr><td style="text-align: center; color: var(--text-muted);">Empty ResultSet.</td></tr>`;
        }

        // 3. Render Alternative Physical Plan Trees
        physicalPlaceholder.classList.add("hidden");
        physicalContainer.classList.remove("hidden");
        
        if (data.physical_plans && data.physical_plans.length >= 3) {
            physicalTreeRenderA.innerHTML = renderPhysicalNode(data.physical_plans[0].tree);
            physicalTreeRenderB.innerHTML = renderPhysicalNode(data.physical_plans[1].tree);
            physicalTreeRenderC.innerHTML = renderPhysicalNode(data.physical_plans[2].tree);
        } else if (data.physical_plan) {
            // Fallback for backward compatibility
            physicalTreeRenderA.innerHTML = renderPhysicalNode(data.physical_plan);
            physicalTreeRenderB.innerHTML = `<p style="color: var(--text-muted); text-align:center; padding-top: 20px;">Plan B not generated.</p>`;
            physicalTreeRenderC.innerHTML = `<p style="color: var(--text-muted); text-align:center; padding-top: 20px;">Plan C not generated.</p>`;
        } else {
            physicalTreeRenderA.innerHTML = `<p style="color: var(--text-muted); text-align:center; padding-top: 20px;">No physical plans available.</p>`;
            physicalTreeRenderB.innerHTML = `<p style="color: var(--text-muted); text-align:center; padding-top: 20px;">No physical plans available.</p>`;
            physicalTreeRenderC.innerHTML = `<p style="color: var(--text-muted); text-align:center; padding-top: 20px;">No physical plans available.</p>`;
        }

        // 4. Render Logical Relational Algebra Trees
        logicalPlaceholder.classList.add("hidden");
        logicalContainer.classList.remove("hidden");
        
        if (data.logical_plan) {
            logicalTreeRender.textContent = formatAlgebraTree(data.logical_plan);
        } else {
            logicalTreeRender.textContent = "No logical plan available.";
        }

        if (data.optimized_plan) {
            optimizedTreeRender.textContent = formatAlgebraTree(data.optimized_plan);
        } else {
            optimizedTreeRender.textContent = "No optimized logical plan available.";
        }

        // 5. Render Parsed AST
        parsedPlaceholder.classList.add("hidden");
        parsedContainer.classList.remove("hidden");
        if (data.parsed_query) {
            parsedTreeRender.textContent = JSON.stringify(data.parsed_query, null, 2);
        } else {
            parsedTreeRender.textContent = "No parsed query AST available.";
        }

        // 6. Render Optimizer Analytics Section (Cost Analysis & Best Plan)
        if (data.cost_analysis && data.best_plan) {
            optimizerSection.classList.remove("hidden");
            
            // Populate Best Plan details
            bestPlanName.textContent = data.best_plan.name;
            bestPlanCost.textContent = data.best_plan.total_cost;
            bestPlanJoin.textContent = data.best_plan.join_algorithm;
            bestPlanScan.textContent = data.best_plan.scan_strategy;
            bestPlanWhy.textContent = data.best_plan.why_selected;
            
            // Populate Cost Analysis comparison table
            let compHtml = "";
            data.cost_analysis.forEach(item => {
                const isBest = item.plan_id === data.best_plan.id;
                const rowClass = isBest ? "class='best-plan-row'" : "";
                compHtml += `
                    <tr ${rowClass}>
                        <td><strong>${item.name}</strong></td>
                        <td>${item.scan_type}</td>
                        <td>${item.join_type}</td>
                        <td>${item.cpu_cost.toLocaleString()}</td>
                        <td>${item.io_cost.toLocaleString()}</td>
                        <td><strong>${item.total_cost.toLocaleString()}</strong></td>
                        <td>${item.estimated_rows.toLocaleString()}</td>
                        <td><span class="badge" style="background-color: ${isBest ? 'var(--color-secondary)' : 'rgba(148,163,184,0.15)'}; border: 1px solid ${isBest ? 'transparent' : 'var(--border-color)'}; color: ${isBest ? '#fff' : 'var(--text-secondary)'}">${item.rank}</span></td>
                    </tr>
                `;
            });
            comparisonTableBody.innerHTML = compHtml;
            
            // Render cost bar chart
            let chartHtml = "";
            const maxCost = Math.max(...data.cost_analysis.map(x => x.total_cost), 1);
            
            data.cost_analysis.forEach(item => {
                const percentage = (item.total_cost / maxCost) * 100;
                const barClass = `chart-bar-rank${item.rank}`;
                chartHtml += `
                    <div class="chart-row">
                        <div class="chart-label">${item.name}</div>
                        <div class="chart-bar-outer">
                            <div class="chart-bar-inner ${barClass}" style="width: ${percentage}%"></div>
                        </div>
                        <div class="chart-value">${item.total_cost}</div>
                    </div>
                `;
            });
            chartBarsList.innerHTML = chartHtml;
        } else {
            optimizerSection.classList.add("hidden");
        }

        // Render Optimizer Comparison Tab Content
        if (data.cost_reduction_pct !== undefined && data.optimization_explanations && data.before_optimization && data.after_optimization) {
            comparisonPlaceholder.classList.add("hidden");
            comparisonContainer.classList.remove("hidden");
            
            reductionPctVal.textContent = `${data.cost_reduction_pct}%`;
            
            comparisonExplanations.innerHTML = data.optimization_explanations.map(exp => {
                return `<li><i class="fa-solid fa-circle-info text-info" style="margin-right: 8px;"></i>${exp}</li>`;
            }).join("");
            
            compLogicalBefore.textContent = formatAlgebraTree(data.before_optimization.logical_tree);
            compLogicalAfter.textContent = formatAlgebraTree(data.after_optimization.logical_tree);
            compCostBefore.textContent = `Cost: ${data.before_optimization.cost.toFixed(2)}`;
            compCostAfter.textContent = `Cost: ${data.after_optimization.cost.toFixed(2)}`;
        } else {
            comparisonPlaceholder.classList.remove("hidden");
            comparisonContainer.classList.add("hidden");
        }

        // Save execution to local history
        const queryText = sqlEditor.value.trim();
        saveToHistory(queryText, data);
    }

    // Recursive formatter for relational algebra tree
    function formatAlgebraTree(node, depth = 0) {
        if (!node) return "";
        let indent = "  ".repeat(depth);
        let prefix = depth === 0 ? "" : "└── ";
        let line = `${indent}${prefix}[${node.node_type}]`;
        
        if (node.node_type === "Projection") {
            line += ` columns: ${node.attributes.columns ? node.attributes.columns.join(', ') : ''}`;
        } else if (node.node_type === "Selection") {
            line += ` condition: ${node.attributes.condition || ''}`;
        } else if (node.node_type === "Join") {
            line += ` type: ${node.attributes.type || 'INNER'}, on: ${node.attributes.on || ''}`;
        } else if (node.node_type === "Scan" || node.node_type === "Relation") {
            line += ` table: ${node.attributes.table || ''}`;
        }
        
        let result = line;
        if (node.children && node.children.length > 0) {
            node.children.forEach(child => {
                result += "\n" + formatAlgebraTree(child, depth + 1);
            });
        }
        return result;
    }

    // Recursive HTML generator for physical plan node visualizer
    function renderPhysicalNode(node) {
        if (!node) return "";
        
        let operatorClass = "node-project";
        let iconClass = "fa-solid fa-arrows-split-up-and-left";
        
        const op = node.operator.toLowerCase();
        if (op.includes("scan") || op.includes("relation")) {
            operatorClass = "node-scan";
            iconClass = "fa-solid fa-magnifying-glass";
        } else if (op.includes("filter")) {
            operatorClass = "node-filter";
            iconClass = "fa-solid fa-filter";
        } else if (op.includes("join")) {
            operatorClass = "node-join";
            iconClass = "fa-solid fa-arrows-spin";
        } else if (op.includes("project")) {
            operatorClass = "node-project";
            iconClass = "fa-solid fa-columns";
        }
        
        // Format details
        let detailsHtml = "";
        if (node.details) {
            for (const [key, val] of Object.entries(node.details)) {
                if (val !== null && val !== undefined) {
                    detailsHtml += `<div><strong>${key}:</strong> ${val}</div>`;
                }
            }
        }
        
        // Generate HTML for children
        let childrenHtml = "";
        if (node.children && node.children.length > 0) {
            childrenHtml = `
                <div class="node-children">
                    ${node.children.map(child => renderPhysicalNode(child)).join("")}
                </div>
            `;
        }
        
        return `
            <div class="plan-node">
                <div class="node-card ${operatorClass}">
                    <div class="node-header">
                        <span class="node-title">${node.operator}</span>
                        <i class="${iconClass} node-type-icon"></i>
                    </div>
                    <div class="node-body">
                        ${detailsHtml}
                    </div>
                    <div class="node-stats">
                        <span><i class="fa-solid fa-bolt"></i> Cost: ${node.cost}</span>
                        <span><i class="fa-solid fa-list-ol"></i> Rows: ${node.rows}</span>
                    </div>
                </div>
                ${childrenHtml}
            </div>
        `;
    }

    function hideAllOutput() {
        metricsPanel.classList.add("hidden");
        
        resultsPlaceholder.classList.remove("hidden");
        resultsContainer.classList.add("hidden");
        
        physicalPlaceholder.classList.remove("hidden");
        physicalContainer.classList.add("hidden");
        
        logicalPlaceholder.classList.remove("hidden");
        logicalContainer.classList.add("hidden");

        parsedPlaceholder.classList.remove("hidden");
        parsedContainer.classList.add("hidden");

        optimizerSection.classList.add("hidden");
        
        comparisonPlaceholder.classList.remove("hidden");
        comparisonContainer.classList.add("hidden");
    }

    function showToast(message) {
        toastMessage.textContent = message;
        errorToast.classList.remove("hidden");
        
        // Automatically hide after 6 seconds
        if (window.toastTimeout) {
            clearTimeout(window.toastTimeout);
        }
        window.toastTimeout = setTimeout(hideToast, 6000);
    }

    function hideToast() {
        errorToast.classList.add("hidden");
    }

    // --- QUERY HISTORY MANAGEMENT ---
    function getHistory() {
        try {
            return JSON.parse(localStorage.getItem("query_history") || "[]");
        } catch (e) {
            return [];
        }
    }

    function saveToHistory(query, data) {
        if (!data || !data.success) return;
        let history = getHistory();
        // Remove duplicate query if exists
        history = history.filter(item => item.query.trim().toLowerCase() !== query.trim().toLowerCase());
        // Add to front
        history.unshift({
            query: query,
            timestamp: new Date().toLocaleTimeString(),
            bestPlan: data.best_plan ? data.best_plan.name : "N/A",
            totalCost: data.best_plan ? data.best_plan.total_cost : "N/A"
        });
        // Limit to 20 items
        if (history.length > 20) {
            history.pop();
        }
        localStorage.setItem("query_history", JSON.stringify(history));
    }

    function renderHistory() {
        const history = getHistory();
        if (history.length === 0) {
            historyList.innerHTML = `
                <div style="text-align: center; padding: 40px 20px; color: var(--text-secondary);">
                    <i class="fa-solid fa-history" style="font-size: 2.5rem; color: var(--border-color); margin-bottom: 12px; display: block;"></i>
                    <p>No queries executed in this session.</p>
                </div>
            `;
            return;
        }

        historyList.innerHTML = history.map((item, index) => {
            return `
                <div class="history-card" style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 16px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; gap: 16px; transition: transform 0.2s, box-shadow 0.2s; cursor: pointer;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)'" onmouseout="this.style.transform='none'; this.style.boxShadow='none'">
                    <div style="flex: 1; min-width: 0;">
                        <pre style="margin: 0; font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%;">${escapeHtml(item.query)}</pre>
                        <div style="display: flex; gap: 16px; font-size: 0.75rem; color: var(--text-secondary); margin-top: 8px; flex-wrap: wrap;">
                            <span><i class="fa-solid fa-clock"></i> ${item.timestamp}</span>
                            <span><i class="fa-solid fa-trophy text-warning"></i> ${item.bestPlan}</span>
                            <span><i class="fa-solid fa-bolt text-accent"></i> Cost: ${item.totalCost}</span>
                        </div>
                    </div>
                    <button class="btn btn-secondary btn-sm btn-load-history" data-index="${index}" style="padding: 6px 12px; font-size: 0.8rem; white-space: nowrap;">
                        <i class="fa-solid fa-folder-open"></i> Load Query
                    </button>
                </div>
            `;
        }).join("");

        // Attach event listeners
        historyList.querySelectorAll(".btn-load-history").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const idx = btn.getAttribute("data-index");
                const item = history[idx];
                if (item) {
                    sqlEditor.value = item.query;
                    sqlEditor.focus();
                    // Switch to Results Tab
                    const resultsTabBtn = document.querySelector('.tab-btn[data-tab="tab-results"]');
                    if (resultsTabBtn) resultsTabBtn.click();
                    runQuery();
                }
            });
        });

        // Also allow clicking the card itself to load
        historyList.querySelectorAll(".history-card").forEach(card => {
            card.addEventListener("click", () => {
                const btn = card.querySelector(".btn-load-history");
                if (btn) btn.click();
            });
        });
    }

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // --- DATABASE STATISTICS LOADING ---
    function loadStatistics() {
        fetch("/api/statistics")
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (statsTotalRecords) statsTotalRecords.textContent = data.total_records.toLocaleString();
                    const heroStatRecords = document.getElementById("heroStatRecords");
                    if (heroStatRecords) heroStatRecords.textContent = data.total_records.toLocaleString();
                    if (statsRowsStudent && data.table_counts.Student !== undefined) statsRowsStudent.textContent = data.table_counts.Student.toLocaleString();
                    if (statsRowsDepartment && data.table_counts.Department !== undefined) statsRowsDepartment.textContent = data.table_counts.Department.toLocaleString();
                    if (statsRowsTeacher && data.table_counts.Teacher !== undefined) statsRowsTeacher.textContent = data.table_counts.Teacher.toLocaleString();
                    if (statsRowsCourse && data.table_counts.Course !== undefined) statsRowsCourse.textContent = data.table_counts.Course.toLocaleString();
                }
            })
            .catch(err => console.error("Error fetching database stats:", err));
    }

    // Initial loads
    renderHistory();
    loadStatistics();
});
