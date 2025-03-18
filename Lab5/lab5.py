import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, CheckButtons
from scipy.signal import butter, filtfilt

INIT_AMPLITUDE = 1.0
INIT_FREQUENCY = 1.0
INIT_PHASE = 0.0
INIT_NOISE_MEAN = 0.0
INIT_NOISE_COV = 0.1
INIT_SHOW_NOISE = True
INIT_FILTER_ORDER = 4
INIT_CUTOFF_FREQ = 2.0

t = np.linspace(0, 2 * np.pi, 1000)
noise = np.random.normal(INIT_NOISE_MEAN, np.sqrt(INIT_NOISE_COV), len(t))

def harmonic_with_noise(amplitude, frequency, phase, noise_mean, noise_covariance, show_noise):
    global noise
    signal = amplitude * np.sin(frequency * t + phase)
    if show_noise:
        return signal + noise
    return signal

def apply_filter(signal, cutoff_freq, order=4):
    nyquist = 0.5 * len(t)
    normal_cutoff = cutoff_freq / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, signal)

fig, ax = plt.subplots()
plt.subplots_adjust(left=0.1, bottom=0.45)

# Початковий графік
raw_signal = harmonic_with_noise(INIT_AMPLITUDE, INIT_FREQUENCY, INIT_PHASE, INIT_NOISE_MEAN, INIT_NOISE_COV, INIT_SHOW_NOISE)
signal_line, = ax.plot(t, raw_signal, lw=2, label="Зашумлена гармоніка", color="#264e43") 
filtered_signal_line, = ax.plot(t, apply_filter(raw_signal, INIT_CUTOFF_FREQ, INIT_FILTER_ORDER), lw=2, linestyle='dashed', label="Фільтрована гармоніка", color="#d3ddc0")
ax.set_title("Гармонічний сигнал із шумом", fontsize=14, color="#264e43")
ax.set_xlabel("Час", fontsize=12, color="#264e43")
ax.set_ylabel("Амплітуда", fontsize=12, color="#264e43")
ax.legend()

ax.grid(True, which='both', axis='both', color='#264e43', linestyle='--', linewidth=0.5)

# Додавання слайдерів
axcolor = '#d3ddc0' 
ax_amp = plt.axes([0.1, 0.3, 0.65, 0.03], facecolor=axcolor)
ax_freq = plt.axes([0.1, 0.25, 0.65, 0.03], facecolor=axcolor)
ax_phase = plt.axes([0.1, 0.2, 0.65, 0.03], facecolor=axcolor)
ax_noise_mean = plt.axes([0.1, 0.15, 0.65, 0.03], facecolor=axcolor)
ax_noise_cov = plt.axes([0.1, 0.1, 0.65, 0.03], facecolor=axcolor)
ax_filter_cutoff = plt.axes([0.1, 0.05, 0.65, 0.03], facecolor=axcolor)

s_amp = Slider(ax_amp, 'Амплітуда', 0.1, 2.0, valinit=INIT_AMPLITUDE, color='#264e43')  
s_freq = Slider(ax_freq, 'Частота', 0.1, 5.0, valinit=INIT_FREQUENCY, color='#264e43')  
s_phase = Slider(ax_phase, 'Фаза', 0, 2*np.pi, valinit=INIT_PHASE, color='#264e43') 
s_noise_mean = Slider(ax_noise_mean, 'Середнє шуму', -1.0, 1.0, valinit=INIT_NOISE_MEAN, color='#264e43')  
s_noise_cov = Slider(ax_noise_cov, 'Дисперсія шуму', 0.01, 1.0, valinit=INIT_NOISE_COV, color='#264e43')  
s_filter_cutoff = Slider(ax_filter_cutoff, 'Зріз частоти', 0.1, 5.0, valinit=INIT_CUTOFF_FREQ, color='#264e43')  

# Додавання чекбоксів
ax_check = plt.axes([0.8, 0.2, 0.15, 0.1], facecolor=axcolor)
check = CheckButtons(ax_check, ['Шум'], [INIT_SHOW_NOISE])
check.labels[0].set_color('black') 

ax_filter_check = plt.axes([0.8, 0.1, 0.15, 0.1], facecolor=axcolor)
filter_check = CheckButtons(ax_filter_check, ['Фільтр'], [True])
filter_check.labels[0].set_color('black') 

# Оновлення графіка
def update(val):
    global noise
    show_noise = check.get_status()[0]
    raw_signal = harmonic_with_noise(s_amp.val, s_freq.val, s_phase.val, s_noise_mean.val, s_noise_cov.val, show_noise)
    signal_line.set_ydata(raw_signal)
    if filter_check.get_status()[0]:
        filtered_signal_line.set_ydata(apply_filter(raw_signal, s_filter_cutoff.val, INIT_FILTER_ORDER))
    else:
        filtered_signal_line.set_ydata(raw_signal * 0) 
    fig.canvas.draw_idle()

s_amp.on_changed(update)
s_freq.on_changed(update)
s_phase.on_changed(update)
s_noise_mean.on_changed(lambda val: update_noise())
s_noise_cov.on_changed(lambda val: update_noise())
s_filter_cutoff.on_changed(update)
check.on_clicked(update)
filter_check.on_clicked(update)

def update_noise():
    global noise
    noise = np.random.normal(s_noise_mean.val, np.sqrt(s_noise_cov.val), len(t))
    update(None)


resetax = plt.axes([0.8, 0.05, 0.1, 0.04])
button = Button(resetax, 'Reset', color='#d3ddc0', hovercolor='#264e43')

def reset(event):
    global noise
    s_amp.reset()
    s_freq.reset()
    s_phase.reset()
    s_noise_mean.reset()
    s_noise_cov.reset()
    s_filter_cutoff.reset()
    check.set_active(0) if not INIT_SHOW_NOISE else check.set_active(0)
    filter_check.set_active(0)
    noise = np.random.normal(INIT_NOISE_MEAN, np.sqrt(INIT_NOISE_COV), len(t))
    update(None)

button.on_clicked(reset)

plt.show()
