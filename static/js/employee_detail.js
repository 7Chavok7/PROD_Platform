/* static/js/employee_detail.js | A.Grachev */
// =========================================================
//   КАРТОЧКА СОТРУДНИКА — УПРАВЛЕНИЕ НАВЫКАМИ
// =========================================================

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('skillsContainer');
    const addBtn = document.getElementById('addSkillBtn');
    const noMsg = document.getElementById('noSkillsMessage');

    // =========================================================
    // 1. ДОБАВЛЕНИЕ НАВЫКА (модальное окно)
    // =========================================================
    addBtn.addEventListener('click', function() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'addSkillModal';
        modal.setAttribute('tabindex', '-1');
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-star me-2"></i>Добавить навык</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Навык</label>
                            <select id="skillSelect" class="form-select">
                                <option value="">Выберите навык...</option>
                                ${document.querySelectorAll('#skillOptions option').forEach(opt => {
                                    modal.innerHTML += `<option value="${opt.value}">${opt.text}</option>`;
                                })}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Уровень владения</label>
                            <select id="levelSelect" class="form-select">
                                <option value="1">1 — Начинающий</option>
                                <option value="2">2 — Базовый</option>
                                <option value="3" selected>3 — Средний</option>
                                <option value="4">4 — Продвинутый</option>
                                <option value="5">5 — Эксперт</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                        <button type="button" class="btn btn-primary" id="saveSkillBtn">Сохранить</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Заполняем select навыками
        const skillSelect = modal.querySelector('#skillSelect');
        document.querySelectorAll('#skillOptions option').forEach(opt => {
            const option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.text;
            if (opt.value) {
                skillSelect.appendChild(option);
            }
        });

        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        modal.querySelector('#saveSkillBtn').addEventListener('click', function() {
            const skillId = modal.querySelector('#skillSelect').value;
            const level = modal.querySelector('#levelSelect').value;

            if (!skillId) {
                alert('Пожалуйста, выберите навык');
                return;
            }

            const employeePk = document.querySelector('[data-employee-pk]').dataset.employeePk;

            fetch(`/employees/${employeePk}/add-skill/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    skill_id: parseInt(skillId),
                    level: parseInt(level)
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (noMsg) noMsg.remove();

                    const skillTag = document.createElement('span');
                    skillTag.className = 'badge bg-primary me-1 mb-1 px-3 py-2 skill-tag';
                    skillTag.dataset.skillId = data.skill_id;
                    skillTag.innerHTML = `
                        ${data.skill_name}
                        <span class="badge bg-light text-dark ms-1">ур. ${data.level}</span>
                        <span class="remove-skill ms-2" title="Удалить навык">✕</span>
                    `;
                    container.appendChild(skillTag);

                    skillTag.querySelector('.remove-skill').addEventListener('click', function(e) {
                        e.stopPropagation();
                        removeSkill(skillTag, data.skill_id);
                    });

                    modalInstance.hide();
                    modal.remove();
                } else {
                    alert('Ошибка: ' + data.error);
                }
            })
            .catch(error => {
                alert('Ошибка при добавлении навыка');
            });
        });

        modal.addEventListener('hidden.bs.modal', function() {
            modal.remove();
        });
    });

    // =========================================================
    // 2. УДАЛЕНИЕ НАВЫКА
    // =========================================================
    function removeSkill(tagElement, skillId) {
        if (!confirm('Удалить этот навык?')) return;

        const employeePk = document.querySelector('[data-employee-pk]').dataset.employeePk;

        fetch(`/employees/${employeePk}/remove-skill/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                skill_id: skillId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                tagElement.remove();
                if (container.querySelectorAll('.skill-tag').length === 0) {
                    container.innerHTML = '<span class="text-muted">Навыки не указаны</span>';
                }
            } else {
                alert('Ошибка: ' + data.error);
            }
        })
        .catch(error => {
            alert('Ошибка при удалении навыка');
        });
    }

    // Навешиваем обработчики на существующие кнопки удаления
    container.querySelectorAll('.remove-skill').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const tag = this.closest('.skill-tag');
            const skillId = tag.dataset.skillId;
            removeSkill(tag, skillId);
        });
    });

    // =========================================================
    // 3. ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: получение CSRF-токена
    // =========================================================
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    console.log('👤 Карточка сотрудника загружена');
});