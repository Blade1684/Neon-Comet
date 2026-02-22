
document.addEventListener('DOMContentLoaded', () => {
    const addBtn = document.getElementById('add-btn');
    const urlInput = document.getElementById('url-input');
    const targetInput = document.getElementById('target-input');
    const emailInput = document.getElementById('email-input');
    const statusMessage = document.getElementById('status-message');
    const productGrid = document.getElementById('product-grid');
    const template = document.getElementById('product-card-template');

    // Load initial products
    fetchProducts();

    async function fetchProducts() {
        try {
            const response = await fetch('/api/products');
            const products = await response.json();
            renderProducts(products);
        } catch (error) {
            console.error('Error fetching products:', error);
            productGrid.innerHTML = '<p style="color:var(--danger)">Failed to load watchlist.</p>';
        }
    }

    function renderProducts(products) {
        productGrid.innerHTML = '';

        if (products.length === 0) {
            productGrid.innerHTML = '<p style="color:var(--text-muted); grid-column:1/-1; text-align:center;">No items in watchlist yet. Add one above! 🚀</p>';
            return;
        }

        products.forEach(product => {
            const clone = template.content.cloneNode(true);

            clone.querySelector('.product-title').textContent = product.title;
            clone.querySelector('.current-price').textContent = `₹${product.current_price.toLocaleString('en-IN')}`;
            clone.querySelector('.target-price').textContent = `₹${product.target_price.toLocaleString('en-IN')}`;
            clone.querySelector('.visit-link').href = product.url;

            // Format time
            const date = new Date(product.last_checked);
            clone.querySelector('.last-checked').textContent = 'Updated: ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            // Edit Action
            const editBtn = clone.querySelector('.edit-btn');
            editBtn.addEventListener('click', () => window.openEditModal(product.id, product.target_price, product.email));

            // Delete Action
            const deleteBtn = clone.querySelector('.delete-btn');
            deleteBtn.addEventListener('click', () => deleteProduct(product.id));

            productGrid.appendChild(clone);
        });
    }

    async function addProduct() {
        const url = urlInput.value.trim();
        const targetPrice = targetInput.value ? parseFloat(targetInput.value) : 0;
        const email = emailInput.value.trim();

        if (!url) {
            setStatus('Please enter a URL', 'error');
            return;
        }

        addBtn.disabled = true;
        addBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Adding...';
        setStatus('Scraping product info...', 'info');

        try {
            const response = await fetch('/api/products', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, target_price: targetPrice, email })
            });

            const data = await response.json();

            if (response.ok) {
                setStatus('Product added successfully!', 'success');
                urlInput.value = '';
                targetInput.value = '';
                fetchProducts(); // Refresh list
            } else {
                setStatus(data.error || 'Failed to add product', 'error');
            }
        } catch (error) {
            setStatus('Network error: ' + error.message, 'error');
        } finally {
            addBtn.disabled = false;
            addBtn.innerHTML = '<i class="fa-solid fa-radar"></i> Track';
        }
    }

    async function deleteProduct(id) {
        if (!confirm('Stop tracking this item?')) return;

        try {
            const response = await fetch(`/api/products/${id}`, { method: 'DELETE' });
            if (response.ok) {
                setStatus('Item deleted.', 'success');
                fetchProducts();
            } else {
                setStatus('Failed to delete item.', 'error');
            }
        } catch (error) {
            setStatus('Error deleting item: ' + error.message, 'error');
        }
    }

    function setStatus(msg, type) {
        statusMessage.textContent = msg;
        statusMessage.style.color = type === 'error' ? 'var(--danger)' : (type === 'success' ? 'var(--success)' : 'var(--text-muted)');
        setTimeout(() => statusMessage.textContent = '', 5000);
    }

    addBtn.addEventListener('click', addProduct);

    // --- Edit Feature ---
    const editModal = document.getElementById('edit-modal');
    const editTargetInput = document.getElementById('edit-target');
    const editEmailInput = document.getElementById('edit-email');
    const saveEditBtn = document.getElementById('save-edit');
    const cancelEditBtn = document.getElementById('cancel-edit');

    let currentEditId = null;

    window.openEditModal = (id, currentTarget, currentEmail) => {
        currentEditId = id;
        editTargetInput.value = currentTarget;
        editEmailInput.value = currentEmail || '';
        editModal.classList.remove('hidden');
    };

    window.closeModal = () => {
        editModal.classList.add('hidden');
        currentEditId = null;
    };

    cancelEditBtn.addEventListener('click', window.closeModal);

    saveEditBtn.addEventListener('click', async () => {
        if (!currentEditId) return;

        const newTarget = parseFloat(editTargetInput.value);
        const newEmail = editEmailInput.value.trim();

        saveEditBtn.disabled = true;
        saveEditBtn.textContent = 'Saving...';

        try {
            const response = await fetch(`/api/products/${currentEditId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_price: newTarget, email: newEmail })
            });

            if (response.ok) {
                window.closeModal();
                fetchProducts(); // Refresh UI
                setStatus('Product updated!', 'success');
            } else {
                setStatus('Failed to update product', 'error');
            }
        } catch (error) {
            console.error(error);
            setStatus('Error updating product: ' + error.message, 'error');
        } finally {
            saveEditBtn.disabled = false;
            saveEditBtn.textContent = 'Save Changes';
        }
    });

    // Close modal on outside click
    editModal.addEventListener('click', (e) => {
        if (e.target === editModal) window.closeModal();
    });

    // --- Check Now Feature ---
    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.addEventListener('click', async () => {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fa-solid fa-rotate fa-spin"></i> Checking...';

        try {
            const response = await fetch('/api/check-now', { method: 'POST' });
            if (response.ok) {
                setStatus('Prices updated successfully!', 'success');
                fetchProducts();
            } else {
                setStatus('Failed to update prices', 'error');
            }
        } catch (error) {
            setStatus('Network error', 'error');
        } finally {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fa-solid fa-rotate"></i> Check Prices Now';
        }
    });
});
