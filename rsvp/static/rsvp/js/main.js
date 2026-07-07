(function () {
    "use strict";

    var config = window.RSVP_CONFIG;

    var stepNames = document.getElementById("step-names");
    var stepSuccess = document.getElementById("step-success");
    var alertBox = document.getElementById("alert-box");
    var modalAlertBox = document.getElementById("modal-alert-box");

    var modalBackdrop = document.getElementById("rsvp-modal-backdrop");
    var btnModalClose = document.getElementById("btn-modal-close");

    var inviteNumberInput = document.getElementById("invite-number");
    var btnBuscar = document.getElementById("btn-buscar");
    var btnVoltar = document.getElementById("btn-voltar");
    var btnConfirmar = document.getElementById("btn-confirmar");
    var btnNovaConsulta = document.getElementById("btn-nova-consulta");
    var btnAddGuest = document.getElementById("btn-add-guest");

    var foundNumber = document.getElementById("found-number");
    var foundPasses = document.getElementById("found-passes");
    var namesFields = document.getElementById("names-fields");
    var alreadyConfirmedMsg = document.getElementById("already-confirmed-msg");

    var currentInvite = null;

    function showAlert(target, message, type) {
        target.textContent = message;
        target.className = "alert alert-" + (type || "danger");
    }

    function hideAlert(target) {
        target.className = "alert d-none";
        target.textContent = "";
    }

    function setLoading(button, loading, defaultText) {
        button.disabled = loading;
        button.textContent = loading ? "Aguarde..." : defaultText;
    }

    function showModalStep(step) {
        stepNames.classList.add("d-none");
        stepSuccess.classList.add("d-none");
        step.classList.remove("d-none");
    }

    function openModal() {
        hideAlert(modalAlertBox);
        modalBackdrop.classList.remove("d-none");
        document.body.classList.add("modal-open");
    }

    function closeModal() {
        modalBackdrop.classList.add("d-none");
        document.body.classList.remove("modal-open");
        hideAlert(modalAlertBox);
        currentInvite = null;
    }

    function postJson(url, payload) {
        return fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": config.csrfToken
            },
            body: JSON.stringify(payload)
        }).then(function (response) {
            return response.json().then(function (data) {
                return { status: response.status, data: data };
            });
        });
    }

    function createNameField(index, value) {
        var wrapper = document.createElement("div");
        wrapper.className = "guest-name-input";

        var label = document.createElement("label");
        label.className = "form-label";
        label.textContent = "Convidado " + (index + 1);

        var input = document.createElement("input");
        input.type = "text";
        input.className = "form-control guest-name";
        input.value = value || "";
        input.placeholder = "Nome completo";
        input.maxLength = 150;

        wrapper.appendChild(label);
        wrapper.appendChild(input);
        return wrapper;
    }

    function updateAddButtonVisibility() {
        var currentCount = namesFields.querySelectorAll(".guest-name").length;
        if (!currentInvite || currentCount >= currentInvite.num_passes) {
            btnAddGuest.classList.add("d-none");
        } else {
            btnAddGuest.classList.remove("d-none");
        }
    }

    function renderNameFields(invite) {
        namesFields.innerHTML = "";

        // Mostra apenas os campos até o último convidado já preenchido
        // (ou só o primeiro, se ainda não houver nenhum nome salvo).
        var initialCount = 1;
        for (var i = invite.num_passes; i >= 1; i--) {
            if (invite.names[i - 1]) {
                initialCount = i;
                break;
            }
        }

        for (var j = 0; j < initialCount; j++) {
            namesFields.appendChild(createNameField(j, invite.names[j]));
        }

        updateAddButtonVisibility();
    }

    function displayInvite(invite) {
        currentInvite = invite;
        foundNumber.textContent = invite.number;
        foundPasses.textContent = invite.num_passes;

        if (invite.confirmed) {
            alreadyConfirmedMsg.textContent = "Presença já confirmada em " + invite.confirmed_at + ". Você pode atualizar os nomes abaixo, se precisar.";
            alreadyConfirmedMsg.classList.remove("d-none");
        } else {
            alreadyConfirmedMsg.classList.add("d-none");
        }

        renderNameFields(invite);
        showModalStep(stepNames);
        openModal();
    }

    btnBuscar.addEventListener("click", function () {
        hideAlert(alertBox);
        var number = inviteNumberInput.value.trim();
        if (!number) {
            showAlert(alertBox, "Digite o número do convite.");
            return;
        }

        setLoading(btnBuscar, true, "Buscar");
        postJson(config.buscarUrl, { number: number })
            .then(function (result) {
                if (result.data.ok) {
                    displayInvite(result.data.invite);
                } else {
                    showAlert(alertBox, result.data.error);
                }
            })
            .catch(function () {
                showAlert(alertBox, "Não foi possível conectar. Tente novamente.");
            })
            .finally(function () {
                setLoading(btnBuscar, false, "Buscar");
            });
    });

    inviteNumberInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            btnBuscar.click();
        }
    });

    btnAddGuest.addEventListener("click", function () {
        if (!currentInvite) {
            return;
        }

        var currentCount = namesFields.querySelectorAll(".guest-name").length;
        if (currentCount >= currentInvite.num_passes) {
            return;
        }

        var field = createNameField(currentCount, currentInvite.names[currentCount]);
        namesFields.appendChild(field);
        field.querySelector("input").focus();

        updateAddButtonVisibility();
    });

    btnVoltar.addEventListener("click", function () {
        closeModal();
    });

    btnModalClose.addEventListener("click", function () {
        closeModal();
    });

    modalBackdrop.addEventListener("click", function (event) {
        if (event.target === modalBackdrop) {
            closeModal();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !modalBackdrop.classList.contains("d-none")) {
            closeModal();
        }
    });

    btnConfirmar.addEventListener("click", function () {
        hideAlert(modalAlertBox);
        if (!currentInvite) {
            return;
        }

        var inputs = namesFields.querySelectorAll(".guest-name");
        var names = [];
        inputs.forEach(function (input) {
            names.push(input.value.trim());
        });
        while (names.length < currentInvite.num_passes) {
            names.push("");
        }

        setLoading(btnConfirmar, true, "Confirmar presença");
        postJson(config.confirmarUrl, { number: currentInvite.number, names: names })
            .then(function (result) {
                if (result.data.ok) {
                    hideAlert(modalAlertBox);
                    showModalStep(stepSuccess);
                } else {
                    showAlert(modalAlertBox, result.data.error);
                }
            })
            .catch(function () {
                showAlert(modalAlertBox, "Não foi possível conectar. Tente novamente.");
            })
            .finally(function () {
                setLoading(btnConfirmar, false, "Confirmar presença");
            });
    });

    btnNovaConsulta.addEventListener("click", function () {
        inviteNumberInput.value = "";
        closeModal();
    });
})();
