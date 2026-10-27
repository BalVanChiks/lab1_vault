const API_BASE = "";

// Универсальная функция для REST
async function api(path, body) {
    const res = await fetch(API_BASE + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });
    
    // Сначала проверяем, успешен ли ответ
    if (!res.ok) {
        // Пробуем получить JSON с ошибкой, если возможно
        try {
            const err = await res.json();
            throw new Error(err.detail || err.message || "Ошибка сервера");
        } catch (e) {
            // Если не JSON, берем текст
            if (e instanceof SyntaxError) {
                const text = await res.text();
                throw new Error(`Сервер вернул ${res.status}: ${text}`);
            }
            throw e;
        }
    }
    
    // Только если всё OK, парсим JSON
    return res.json();
}

// Универсальная функция для GraphQL
async function gql(query, variables = {}) {
    const token = localStorage.getItem("token");
    const res = await fetch("/graphql", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ query, variables })
    });
    
    if (!res.ok) {
        try {
            const err = await res.json();
            throw new Error(err.errors?.[0]?.message || "GraphQL error");
        } catch (e) {
            if (e instanceof SyntaxError) {
                const text = await res.text();
                throw new Error(`GraphQL сервер вернул ${res.status}: ${text}`);
            }
            throw e;
        }
    }
    
    const data = await res.json();
    if (data.errors) throw new Error(data.errors[0].message);
    return data.data;
}

async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const errorElement = document.getElementById("login-error");
    
    try {
        errorElement.innerText = "";
        const data = await api("/auth/login", { email, password });
        localStorage.setItem("token", data.access_token);
        document.getElementById("login-block").classList.add("hidden");
        document.getElementById("admin-block").classList.remove("hidden");
        loadClients();
    } catch (e) {
        console.error("Login error:", e);
        errorElement.innerText = e.message || "Ошибка входа";
    }
}

function logout() {
    localStorage.removeItem("token");
    document.getElementById("login-block").classList.remove("hidden");
    document.getElementById("admin-block").classList.add("hidden");
    document.getElementById("email").value = "";
    document.getElementById("password").value = "";
    document.getElementById("login-error").innerText = "";
}

async function loadClients() {
    try {
        const data = await gql(`{ clients { name clientId isConfidential } }`);
        const tbody = document.querySelector("#clients-table tbody");
        tbody.innerHTML = "";
        data.clients.forEach(c => {
            tbody.innerHTML += `<tr><td>${c.name}</td><td>${c.clientId}</td><td>${c.isConfidential ? "Да" : "Нет"}</td></tr>`;
        });
    } catch (e) {
        console.error("Load clients error:", e);
        alert("Ошибка загрузки клиентов: " + e.message);
    }
}

async function createClient() {
    const name = prompt("Введите имя клиента:");
    if (!name) return;
    try {
        await gql(
            `mutation($name: String!) { createClient(name: $name, isConfidential: false) { clientId } }`,
            { name }
        );
        loadClients();
    } catch (e) {
        alert("Ошибка: " + e.message);
    }
}

// Авто-вход, если токен есть
if (localStorage.getItem("token")) {
    document.getElementById("login-block").classList.add("hidden");
    document.getElementById("admin-block").classList.remove("hidden");
    loadClients();
}