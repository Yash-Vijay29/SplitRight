(() => {
    const alertBox = document.getElementById("alertBox");
    const meBox = document.getElementById("meBox");
    const groupMembersBox = document.getElementById("groupMembersBox");
    const expensesBox = document.getElementById("expensesBox");
    const balancesBox = document.getElementById("balancesBox");
    const settlementsBox = document.getElementById("settlementsBox");
    const groupSelect = document.getElementById("groupSelect");
    const authState = document.getElementById("authState");

    const splitType = document.getElementById("splitType");
    const equalSplitLabel = document.getElementById("equalSplitLabel");
    const unequalSplitLabel = document.getElementById("unequalSplitLabel");
    const splitUserIds = document.getElementById("splitUserIds");
    const splitJson = document.getElementById("splitJson");

    const state = {
        accessToken: localStorage.getItem("sr_access") || "",
        refreshToken: localStorage.getItem("sr_refresh") || "",
        selectedGroupId: localStorage.getItem("sr_group_id") || "",
    };

    function setAuthState() {
        authState.textContent = state.accessToken ? "Logged in" : "Logged out";
    }

    function showAlert(message, kind = "ok") {
        alertBox.classList.remove("hidden", "ok", "error");
        alertBox.classList.add(kind === "error" ? "error" : "ok");
        alertBox.textContent = message;
    }

    function parseApiError(payload, fallback = "Request failed.") {
        if (!payload) {
            return fallback;
        }
        if (typeof payload === "string") {
            return payload;
        }
        if (payload.detail) {
            return String(payload.detail);
        }
        if (payload.message) {
            return String(payload.message);
        }
        const entries = Object.entries(payload)
            .map(([key, value]) => {
                if (Array.isArray(value)) {
                    return `${key}: ${value.join(", ")}`;
                }
                if (typeof value === "object" && value !== null) {
                    return `${key}: ${JSON.stringify(value)}`;
                }
                return `${key}: ${value}`;
            })
            .join(" | ");
        return entries || fallback;
    }

    async function apiRequest(path, options = {}) {
        const headers = {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        };

        if (state.accessToken) {
            headers.Authorization = `Bearer ${state.accessToken}`;
        }

        const response = await fetch(`/api/${path}`, {
            method: options.method || "GET",
            headers,
            body: options.body ? JSON.stringify(options.body) : undefined,
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(parseApiError(data, `HTTP ${response.status}`));
        }
        return data;
    }

    function renderJson(target, payload) {
        target.textContent = JSON.stringify(payload, null, 2);
    }

    function selectedGroupIdOrThrow() {
        const groupId = groupSelect.value || state.selectedGroupId;
        if (!groupId) {
            throw new Error("Select a group first.");
        }
        return groupId;
    }

    async function loadMe() {
        const me = await apiRequest("users/me");
        renderJson(meBox, me);
        return me;
    }

    async function loadGroups() {
        const payload = await apiRequest("groups");
        const groups = payload.results || [];

        const previous = groupSelect.value || state.selectedGroupId;
        groupSelect.innerHTML = '<option value="">Select a group</option>';

        for (const group of groups) {
            const option = document.createElement("option");
            option.value = String(group.group_id);
            option.textContent = `#${group.group_id} - ${group.group_name}`;
            groupSelect.appendChild(option);
        }

        if (previous && groups.some((g) => String(g.group_id) === String(previous))) {
            groupSelect.value = String(previous);
            state.selectedGroupId = String(previous);
            localStorage.setItem("sr_group_id", state.selectedGroupId);
        }

        renderJson(groupMembersBox, payload);
        return payload;
    }

    async function loadGroupMembers() {
        const groupId = selectedGroupIdOrThrow();
        const payload = await apiRequest(`groups/${groupId}/members`);
        renderJson(groupMembersBox, payload);
        return payload;
    }

    async function loadExpenses() {
        const groupId = selectedGroupIdOrThrow();
        const payload = await apiRequest(`groups/${groupId}/expenses`);
        renderJson(expensesBox, payload);
        return payload;
    }

    async function loadBalances() {
        const groupId = selectedGroupIdOrThrow();
        const payload = await apiRequest(`groups/${groupId}/balances`);
        renderJson(balancesBox, payload);
        return payload;
    }

    async function loadPairwise() {
        const groupId = selectedGroupIdOrThrow();
        const payload = await apiRequest(`groups/${groupId}/balances/pairwise`);
        renderJson(balancesBox, payload);
        return payload;
    }

    async function loadMyBalances() {
        const payload = await apiRequest("users/me/balances");
        renderJson(balancesBox, payload);
        return payload;
    }

    async function loadSettlements() {
        const groupId = selectedGroupIdOrThrow();
        const payload = await apiRequest(`groups/${groupId}/settlements`);
        renderJson(settlementsBox, payload);
        return payload;
    }

    document.getElementById("signupForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);

        try {
            const payload = await apiRequest("auth/signup", {
                method: "POST",
                body: {
                    name: form.get("name"),
                    email: form.get("email"),
                    password: form.get("password"),
                },
            });
            showAlert(payload.message || "Signup successful.");
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    document.getElementById("loginForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);

        try {
            const payload = await apiRequest("auth/login", {
                method: "POST",
                body: {
                    email: form.get("email"),
                    password: form.get("password"),
                },
            });

            state.accessToken = payload.access || "";
            state.refreshToken = payload.refresh || "";
            localStorage.setItem("sr_access", state.accessToken);
            localStorage.setItem("sr_refresh", state.refreshToken);
            setAuthState();

            await Promise.all([loadMe(), loadGroups()]);
            showAlert(payload.message || "Login successful.");
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    document.getElementById("createGroupForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);

        try {
            const payload = await apiRequest("groups", {
                method: "POST",
                body: {
                    group_name: form.get("group_name"),
                },
            });
            await loadGroups();
            showAlert(payload.message || "Group created.");
            event.currentTarget.reset();
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    document.getElementById("joinGroupForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);

        try {
            const groupId = Number(form.get("group_id"));
            const payload = await apiRequest(`groups/${groupId}/join`, {
                method: "POST",
            });
            await loadGroups();
            showAlert(payload.message || "Joined group.");
            event.currentTarget.reset();
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    document.getElementById("refreshGroupsBtn").addEventListener("click", async () => {
        try {
            await loadGroups();
            showAlert("Groups refreshed.");
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    groupSelect.addEventListener("change", async (event) => {
        state.selectedGroupId = event.target.value;
        localStorage.setItem("sr_group_id", state.selectedGroupId);

        if (!state.selectedGroupId) {
            return;
        }

        try {
            await Promise.all([loadGroupMembers(), loadExpenses(), loadBalances(), loadSettlements()]);
            showAlert("Group data loaded.");
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    splitType.addEventListener("change", () => {
        const isEqual = splitType.value === "equal";
        equalSplitLabel.classList.toggle("hidden", !isEqual);
        unequalSplitLabel.classList.toggle("hidden", isEqual);
    });

    document.getElementById("expenseForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);

        try {
            const groupId = selectedGroupIdOrThrow();
            const payload = {
                paid_by: Number(form.get("paid_by")),
                amount: String(form.get("amount")),
                expense_date: form.get("expense_date"),
                description: form.get("description"),
                split_type: form.get("split_type"),
            };

            if (payload.split_type === "equal") {
                const ids = String(splitUserIds.value || "")
                    .split(",")
                    .map((entry) => Number(entry.trim()))
                    .filter((entry) => Number.isFinite(entry) && entry > 0);
                payload.split_user_ids = ids;
            } else {
                const raw = splitJson.value || "[]";
                payload.splits = JSON.parse(raw);
            }

            const response = await apiRequest(`groups/${groupId}/expenses`, {
                method: "POST",
                body: payload,
            });

            await loadExpenses();
            await loadBalances();
            showAlert(response.message || "Expense added.");
            event.currentTarget.reset();
            splitUserIds.value = "";
            splitJson.value = "";
            splitType.dispatchEvent(new Event("change"));
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    document.getElementById("settlementForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);

        try {
            const groupId = selectedGroupIdOrThrow();
            const response = await apiRequest(`groups/${groupId}/settlements`, {
                method: "POST",
                body: {
                    from_user: Number(form.get("from_user")),
                    to_user: Number(form.get("to_user")),
                    amount: String(form.get("amount")),
                    settlement_date: form.get("settlement_date"),
                },
            });

            await Promise.all([loadSettlements(), loadBalances()]);
            showAlert(response.message || "Settlement recorded.");
            event.currentTarget.reset();
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    document.getElementById("loadExpensesBtn").addEventListener("click", async () => {
        try {
            await loadExpenses();
            showAlert("Expenses loaded.");
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    document.getElementById("loadBalancesBtn").addEventListener("click", async () => {
        try {
            await loadBalances();
            showAlert("Group balances loaded.");
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    document.getElementById("loadPairwiseBtn").addEventListener("click", async () => {
        try {
            await loadPairwise();
            showAlert("Pairwise balances loaded.");
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    document.getElementById("loadMyBalancesBtn").addEventListener("click", async () => {
        try {
            await loadMyBalances();
            showAlert("My balances loaded.");
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    document.getElementById("loadSettlementsBtn").addEventListener("click", async () => {
        try {
            await loadSettlements();
            showAlert("Settlements loaded.");
        } catch (error) {
            showAlert(error.message, "error");
        }
    });

    setAuthState();
    splitType.dispatchEvent(new Event("change"));

    if (state.accessToken) {
        Promise.all([loadMe(), loadGroups()]).catch((error) => {
            showAlert(error.message, "error");
        });
    }
})();
