// static/js/pomodoro.js

const PomodoroTimer = {
    // --- Configuration ---
    elements: {
        container: null,
        timeDisplay: null,
        statusDisplay: null,
        startButton: null,
        pauseButton: null,
        resetButton: null,
        skipBreakButton: null,
        alarmSoundSelect: null,
        backgroundSoundSelect: null,
        backgroundSoundVolume: null,
    },

    settings: {
        workDuration: 25 * 60,       // seconds
        shortBreakDuration: 5 * 60,  // seconds
        longBreakDuration: 15 * 60,  // seconds
        sessionsBeforeLongBreak: 4,
        defaultAlarmSound: '',       // سيتم تحميله من select
        defaultBackgroundSound: 'none',
        defaultBackgroundVolume: 0.5,
    },

    state: {
        timerInterval: null,
        timeLeft: 0,                 // seconds
        currentMode: 'work',       // 'work', 'shortBreak', 'longBreak'
        isPaused: true,            // يبدأ متوقفًا
        sessionsCompleted: 0,
    },

    audio: {
        alarm: new Audio(),
        background: new Audio(),
    },

    // --- Initialization ---
    init: function () {
        // ربط عناصر DOM
        this.elements.container = document.querySelector('.pomodoro-timer-container');
        if (!this.elements.container) {
            // console.warn("Pomodoro timer container not found. Timer will not initialize.");
            return; // لا يمكن تهيئة المؤقت بدون الحاوية الرئيسية
        }

        this.elements.timeDisplay = document.getElementById('pomodoro-time-display');
        this.elements.statusDisplay = document.getElementById('pomodoro-status');
        this.elements.startButton = document.getElementById('pomodoro-start');
        this.elements.pauseButton = document.getElementById('pomodoro-pause');
        this.elements.resetButton = document.getElementById('pomodoro-reset');
        this.elements.skipBreakButton = document.getElementById('pomodoro-skip-break');
        this.elements.alarmSoundSelect = document.getElementById('alarm-sound-select');
        this.elements.backgroundSoundSelect = document.getElementById('background-sound-select');
        this.elements.backgroundSoundVolume = document.getElementById('background-sound-volume');

        // تحميل الإعدادات من data-attributes
        this.loadSettingsFromDOM();
        
        if (this.audio.background) this.audio.background.loop = true;

        // ربط مستمعي الأحداث
        this.bindEvents();

        // التهيئة الأولية لحالة المؤقت والعرض
        this.resetTimer('work');
    },

    loadSettingsFromDOM: function () {
        if (this.elements.container) {
            this.settings.workDuration = parseInt(this.elements.container.dataset.workDuration) * 60 || this.settings.workDuration;
            this.settings.shortBreakDuration = parseInt(this.elements.container.dataset.shortBreakDuration) * 60 || this.settings.shortBreakDuration;
            this.settings.longBreakDuration = parseInt(this.elements.container.dataset.longBreakDuration) * 60 || this.settings.longBreakDuration;
            this.settings.sessionsBeforeLongBreak = parseInt(this.elements.container.dataset.sessionsBeforeLongBreak) || this.settings.sessionsBeforeLongBreak;
        }
        if (this.elements.alarmSoundSelect) {
            this.settings.defaultAlarmSound = this.elements.alarmSoundSelect.value;
        }
        if (this.elements.backgroundSoundSelect) {
            this.settings.defaultBackgroundSound = this.elements.backgroundSoundSelect.value;
        }
        if (this.elements.backgroundSoundVolume) {
            this.settings.defaultBackgroundVolume = parseFloat(this.elements.backgroundSoundVolume.value);
            if (this.audio.background) this.audio.background.volume = this.settings.defaultBackgroundVolume;
        }
    },

    bindEvents: function () {
        if (this.elements.startButton) this.elements.startButton.addEventListener('click', () => this.start());
        if (this.elements.pauseButton) this.elements.pauseButton.addEventListener('click', () => this.pause());
        if (this.elements.resetButton) this.elements.resetButton.addEventListener('click', () => this.resetTimer('work'));
        if (this.elements.skipBreakButton) this.elements.skipBreakButton.addEventListener('click', () => this.skipBreak());

        if (this.elements.alarmSoundSelect) {
            this.elements.alarmSoundSelect.addEventListener('change', (e) => {
                this.settings.defaultAlarmSound = e.target.value;
            });
        }
        if (this.elements.backgroundSoundSelect) {
            this.elements.backgroundSoundSelect.addEventListener('change', (e) => {
                this.settings.defaultBackgroundSound = e.target.value;
                this.playBackgroundSound(); // تشغيل الصوت الجديد أو إيقافه إذا كان 'none'
            });
        }
        if (this.elements.backgroundSoundVolume) {
            this.elements.backgroundSoundVolume.addEventListener('input', (e) => {
                this.settings.defaultBackgroundVolume = parseFloat(e.target.value);
                if (this.audio.background && !this.audio.background.paused) {
                    this.audio.background.volume = this.settings.defaultBackgroundVolume;
                }
            });
        }
    },

    // --- Core Timer Logic ---
    updateDisplay: function () {
        if (!this.elements.timeDisplay) return;
        const minutes = Math.floor(this.state.timeLeft / 60);
        const seconds = this.state.timeLeft % 60;
        this.elements.timeDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        document.title = `${this.elements.timeDisplay.textContent} - ${this.getModeText(this.state.currentMode)}`;
    },

    getModeText: function (mode) {
        switch (mode) {
            case 'work': return 'وقت العمل';
            case 'shortBreak': return 'راحة قصيرة';
            case 'longBreak': return 'راحة طويلة';
            default: return 'جاهز';
        }
    },

    playAlarmSound: function () {
        if (!this.audio.alarm || this.settings.defaultAlarmSound === 'none') return;
        this.audio.alarm.src = this.settings.defaultAlarmSound;
        this.audio.alarm.play().catch(e => console.error("Error playing alarm sound:", e));
    },

    playBackgroundSound: function () {
        if (!this.audio.background) return;
        if (this.settings.defaultBackgroundSound !== 'none') {
            if (this.audio.background.src !== this.settings.defaultBackgroundSound) {
                this.audio.background.src = this.settings.defaultBackgroundSound;
            }
            this.audio.background.volume = this.settings.defaultBackgroundVolume;
            // تأخير بسيط قبل التشغيل لتجنب أخطاء "interrupted by a new load request"
            setTimeout(() => {
                this.audio.background.play().catch(e => console.error("Error playing background sound:", e));
            }, 150);
        } else {
            this.audio.background.pause();
            this.audio.background.currentTime = 0;
        }
    },

    start: function () {
        if (this.state.isPaused) { // استئناف
            this.state.isPaused = false;
            // لا حاجة لتغيير نص الزر هنا، فقط الحالة
        } else { // بدء جديد
            this.state.isPaused = false;
            this.state.sessionsCompleted = (this.state.currentMode === 'work') ? this.state.sessionsCompleted : 0; // إعادة تعيين الجلسات إذا بدأنا عمل من جديد
            if (this.state.currentMode === 'work') this.playBackgroundSound();
        }
        
        this.updateButtonStates();
        if (this.elements.statusDisplay) this.elements.statusDisplay.textContent = `في وضع: ${this.getModeText(this.state.currentMode)}`;

        clearInterval(this.state.timerInterval); // مسح أي مؤقت سابق
        this.state.timerInterval = setInterval(() => {
            if (this.state.isPaused) return;

            this.state.timeLeft--;
            this.updateDisplay();

            if (this.state.timeLeft < 0) {
                clearInterval(this.state.timerInterval);
                this.playAlarmSound();
                this.switchMode();
            }
        }, 1000);
    },

    pause: function () {
        this.state.isPaused = true;
        clearInterval(this.state.timerInterval);
        this.updateButtonStates();
        if (this.elements.statusDisplay) this.elements.statusDisplay.textContent = `متوقف مؤقتًا: ${this.getModeText(this.state.currentMode)}`;
        if (this.audio.background) this.audio.background.pause();
    },

    resetTimer: function (mode = 'work', fromSkip = false) {
        clearInterval(this.state.timerInterval);
        this.state.isPaused = true;
        this.state.currentMode = mode;

        switch (mode) {
            case 'work':
                this.state.timeLeft = this.settings.workDuration;
                if (!fromSkip) this.state.sessionsCompleted = 0;
                break;
            case 'shortBreak':
                this.state.timeLeft = this.settings.shortBreakDuration;
                break;
            case 'longBreak':
                this.state.timeLeft = this.settings.longBreakDuration;
                break;
        }
        
        this.updateDisplay();
        if (this.elements.statusDisplay) this.elements.statusDisplay.textContent = `جاهز لوضع: ${this.getModeText(this.state.currentMode)}`;
        this.updateButtonStates();
        if (this.audio.background) {
            this.audio.background.pause();
            this.audio.background.currentTime = 0;
        }
    },

    switchMode: function () {
        if (this.state.currentMode === 'work') {
            this.state.sessionsCompleted++;
            if (this.state.sessionsCompleted % this.settings.sessionsBeforeLongBreak === 0) {
                this.resetTimer('longBreak', true);
            } else {
                this.resetTimer('shortBreak', true);
            }
        } else { // كان في وضع راحة
            this.resetTimer('work', true); // true لمنع إعادة تعيين sessionsCompleted بشكل كامل
        }
        // لا تبدأ المؤقت تلقائياً بعد التبديل، دع المستخدم يبدأه
        // إذا أردت بدء الراحة تلقائياً: if (this.state.currentMode !== 'work') this.start();
    },
    
    skipBreak: function () {
        if (this.state.currentMode !== 'work') {
            this.playAlarmSound(); // كإشارة أن الراحة انتهت
            this.resetTimer('work', true);
        }
    },

    updateButtonStates: function() {
        if (!this.elements.startButton || !this.elements.pauseButton || !this.elements.resetButton || !this.elements.skipBreakButton) return;

        if (this.state.isPaused) {
            this.elements.startButton.disabled = false;
            this.elements.startButton.innerHTML = '<i class="fas fa-play"></i> ' + (this.state.timeLeft < (this.state.currentMode === 'work' ? this.settings.workDuration : (this.state.currentMode === 'shortBreak' ? this.settings.shortBreakDuration : this.settings.longBreakDuration)) && this.state.timeLeft > 0 ? 'استئناف' : 'ابدأ');
            this.elements.startButton.classList.remove('btn-info'); // إزالة فئة الاستئناف
            this.elements.startButton.classList.add('btn-success');
            this.elements.pauseButton.disabled = true;
        } else { // المؤقت يعمل
            this.elements.startButton.disabled = true;
            this.elements.pauseButton.disabled = false;
        }
        this.elements.resetButton.disabled = false; // يمكن إعادة التعيين دائمًا
        this.elements.skipBreakButton.disabled = (this.state.currentMode === 'work' || this.state.isPaused);
    }
};

// تهيئة المؤقت عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
    PomodoroTimer.init();
});