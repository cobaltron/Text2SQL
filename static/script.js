document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('queryForm');
    const input = document.getElementById('queryInput');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('span');
    const spinner = document.getElementById('loadingSpinner');
    
    const resultsSection = document.getElementById('resultsSection');
    const sqlCode = document.getElementById('sqlCode');
    const contextCode = document.getElementById('contextCode');
    
    const toggleContextBtn = document.getElementById('toggleContextBtn');
    const contextBody = document.getElementById('contextBody');
    const copyTextBtn = document.getElementById('copyTextBtn');
    
    const errorToast = document.getElementById('errorToast');
    const errorMsg = document.getElementById('errorMsg');
    
    let isGenerating = false;

    // Toggle Context View
    toggleContextBtn.addEventListener('click', () => {
        contextBody.classList.toggle('hide');
        toggleContextBtn.classList.toggle('rotated');
    });

    // Copy SQL to clipboard
    copyTextBtn.addEventListener('click', async () => {
        const text = sqlCode.textContent;
        if (!text) return;
        
        try {
            await navigator.clipboard.writeText(text);
            
            // Temporary icon change to show success
            const originalHTML = copyTextBtn.innerHTML;
            copyTextBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
            
            setTimeout(() => {
                copyTextBtn.innerHTML = originalHTML;
            }, 2000);
        } catch (err) {
            showError('Failed to copy to clipboard');
        }
    });

    // Handle Form Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const query = input.value.trim();
        if (!query || isGenerating) return;
        
        setLoadingState(true);
        errorToast.classList.add('hide');
        resultsSection.classList.add('hide');
        contextBody.classList.add('hide'); // Reset contextual view
        toggleContextBtn.classList.remove('rotated');
        
        try {
            const response = await fetch('/api/generate-sql', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to generate SQL');
            }
            
            const data = await response.json();
            
            // Populate results
            sqlCode.textContent = data.sql;
            contextCode.textContent = data.context;
            
            // Highlight syntax
            hljs.highlightElement(sqlCode);
            hljs.highlightElement(contextCode);
            
            // Show results
            resultsSection.classList.remove('hide');
            
        } catch (err) {
            console.error(err);
            showError(err.message);
        } finally {
            setLoadingState(false);
        }
    });
    
    function setLoadingState(isLoading) {
        isGenerating = isLoading;
        input.disabled = isLoading;
        submitBtn.disabled = isLoading;
        
        if (isLoading) {
            btnText.textContent = 'Generating...';
            spinner.classList.remove('hide');
        } else {
            btnText.textContent = 'Generate';
            spinner.classList.add('hide');
        }
    }
    
    function showError(message) {
        errorMsg.textContent = message;
        errorToast.classList.remove('hide');
        
        setTimeout(() => {
            errorToast.classList.add('hide');
        }, 5000);
    }
});
