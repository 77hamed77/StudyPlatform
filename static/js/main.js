// static/js/main.js

/**
 * دالة مساعدة للحصول على قيمة CSRF token من الكوكيز.
 * @param {string} name - اسم الكوكي (عادة 'csrftoken').
 * @returns {string|null} - قيمة الكوكي أو null إذا لم يتم العثور عليها.
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // هل يبدأ الكوكي بالاسم الذي نريده؟
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * تهيئة وظيفة تبديل المظهر (ليلي/نهاري).
 */
function initializeThemeToggle() {
    const themeToggleButton = document.getElementById('theme-toggle-btn');
    const darkModeStylesheet = document.getElementById('dark-mode-stylesheet');
    const body = document.body;
    const themeIcon = themeToggleButton ? themeToggleButton.querySelector('i') : null;

    if (!themeToggleButton || !darkModeStylesheet || !body || !themeIcon) {
        // console.warn("Theme toggle elements not found. Theme switching disabled.");
        return; // الخروج إذا لم تكن جميع العناصر موجودة
    }

    // الدالة لتطبيق المظهر وتحديث الأيقونة
    const applyTheme = (isDarkMode) => {
        body.classList.toggle('dark-mode', isDarkMode);
        darkModeStylesheet.disabled = !isDarkMode;
        themeIcon.classList.toggle('fa-sun', isDarkMode);
        themeIcon.classList.toggle('fa-moon', !isDarkMode);
        themeToggleButton.setAttribute('title', isDarkMode ? 'تبديل إلى الوضع النهاري' : 'تبديل إلى الوضع الليلي');
    };

    // تحميل التفضيل الأولي عند تحميل الصفحة
    // الخادم يضع فئة .dark-mode على body إذا كان المستخدم قد اختاره
    // هنا نتأكد فقط من أن الأيقونة والـ stylesheet متزامنة مع حالة الـ body
    const serverPrefersDark = body.classList.contains('dark-mode');
    applyTheme(serverPrefersDark); // تطبيق الحالة الأولية

    // إضافة مستمع الحدث لزر التبديل
    themeToggleButton.addEventListener('click', function () {
        const newDarkModeState = !body.classList.contains('dark-mode');
        applyTheme(newDarkModeState);

        // حفظ التفضيل في localStorage (مفيد للمستخدمين غير المسجلين أو كاحتياطي)
        localStorage.setItem('darkModeEnabled', newDarkModeState.toString());

        // إذا كان المستخدم مسجلاً دخوله، أرسل التفضيل للخادم
        const isAuthenticated = body.dataset.isAuthenticated === 'true';
        // const settingsUrl = this.dataset.settingsUrl; // الأفضل تمرير المسار من القالب
        // استخدام مسار ثابت كبديل إذا لم يتم تمرير data-settings-url
        const settingsUrl = body.dataset.settingsUrl || '/settings/';


        if (isAuthenticated && settingsUrl) {
            const csrfToken = getCookie('csrftoken');
            if (!csrfToken) {
                console.error("CSRF token not found. Cannot save theme preference to server.");
                return;
            }

            fetch(settingsUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `dark_mode_enabled=${newDarkModeState ? 'on' : ''}&update_theme_only=true`
            })
            .then(response => {
                if (!response.ok) {
                    console.error('Failed to save theme preference to server. Status:', response.status);
                    // يمكنك هنا إعادة المظهر للحالة السابقة إذا فشل الحفظ في الخادم
                    // applyTheme(!newDarkModeState);
                    // localStorage.setItem('darkModeEnabled', (!newDarkModeState).toString());
                }
                // لا حاجة لـ .json() إذا لم تكن تتوقع استجابة JSON
            })
            .catch(error => {
                console.error('Error saving theme preference to server:', error);
                // نفس التعامل مع الخطأ أعلاه
            });
        }
    });
}

/**
 * تهيئة وظيفة زر "العودة إلى الأعلى".
 */
function initializeScrollToTopButton() {
    const scrollToTopBtn = document.getElementById("scrollToTopBtn");

    if (!scrollToTopBtn) {
        // console.warn("Scroll to top button not found.");
        return;
    }

    // متغير لتتبع حالة الرؤية لتجنب إعادة الرسم غير الضرورية
    let isButtonVisible = false;

    const scrollFunction = () => {
        const shouldBeVisible = (document.body.scrollTop > 150 || document.documentElement.scrollTop > 150);

        if (shouldBeVisible && !isButtonVisible) {
            scrollToTopBtn.style.display = "block";
            // تأخير طفيف لإعطاء فرصة لـ CSS transition للعمل بشكل صحيح على 'display'
            requestAnimationFrame(() => { // استخدام requestAnimationFrame لتحسين الأداء
                scrollToTopBtn.style.opacity = "1";
                scrollToTopBtn.style.visibility = "visible";
            });
            isButtonVisible = true;
        } else if (!shouldBeVisible && isButtonVisible) {
            scrollToTopBtn.style.opacity = "0";
            // تأخير الإخفاء للسماح بتأثير opacity
            // visibility: hidden يتم التحكم بها عبر CSS transition الآن
            // نستخدم setTimeout فقط لإخفاء display بعد انتهاء الـ transition
            setTimeout(() => {
                // تحقق مرة أخرى قبل الإخفاء التام
                if (!(document.body.scrollTop > 150 || document.documentElement.scrollTop > 150)) {
                     scrollToTopBtn.style.display = "none";
                }
            }, 300); // يجب أن يتطابق هذا الوقت مع مدة الـ transition-duration في CSS
            isButtonVisible = false;
        }
    };

    window.addEventListener('scroll', scrollFunction);

    scrollToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}


// استدعاء الدوال عند تحميل الـ DOM
document.addEventListener('DOMContentLoaded', function () {
    initializeThemeToggle();
    initializeScrollToTopButton();

    // يمكنك إضافة أي تهيئات أخرى هنا، مثل:
    // - تفعيل الـ tooltips الخاصة بـ Bootstrap
    // const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    // const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    //   return new bootstrap.Tooltip(tooltipTriggerEl);
    // });

    // - تفعيل الـ popovers
    // const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    // const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    //   return new bootstrap.Popover(popoverTriggerEl);
    // });
});