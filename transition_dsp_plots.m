% transition_dsp_plots.m
% Song transition analyzer: plots that show each DSP tool at work, grouped by metric.
% Loads transition_data.mat (deck A -> deck B; song names are in the file).
% Runs in base MATLAB (no toolboxes) and GNU Octave. PNGs go to ./figures.
%
%   Metric 1  Tempo      m1a sampling, m1b STFT, m1c spectral flux + beat grid, m1d Fourier tempogram
%   Metric 2  Key        m2a spectral peaks, m2b chromagram, m2c key profiles, m2d circular-shift search
%   Metric 3  Spectrum   m3a band energy, m3b frequency/phase response, m3c pole-zero, m3d impulse/step, m3e handoff ramp
%   Metric 4  Structure  m4a framed loudness, m4b self-similarity, m4c checkerboard kernel, m4d novelty
%   Compare   c1 cross-correlation, c2 cross-similarity, c3 output spectrogram, c4 weighted score

clear; close all;
load('transition_data.mat');
sr = double(sr); hop = double(hop); nfft = double(nfft); shift = double(shift);   % integers from the .mat -> double
if ~exist('figures', 'dir'), mkdir('figures'); end

cA = [0.165 0.471 0.839]; cB = [0.922 0.408 0.204]; cG = [0.106 0.686 0.478]; cY = [0.929 0.631 0];
cX = [0.72 0.96 0.82]; gry = [.6 .6 .6]; ink = [.05 .05 .05]; fs = 11;
ramp = @(c) [linspace(1, c(1), 64)' linspace(1, c(2), 64)' linspace(1, c(3), 64)'];
div  = [[linspace(cA(1),1,32)' linspace(cA(2),1,32)' linspace(cA(3),1,32)']; [linspace(1,cB(1),32)' linspace(1,cB(2),32)' linspace(1,cB(3),32)']];
mmss = @(t) sprintf('%d:%02d', floor(t/60), round(mod(t,60)));
newfig = @(w,h) figure('Visible','off','Color','w','Units','pixels','Position',[100 100 w h],'PaperPositionMode','auto');
save_png = @(name) print(gcf, fullfile('figures', name), '-dpng', '-r150');
vline = @(x, y, sty, c) plot([x x], y, sty, 'Color', c);
notes = cellstr(notes);

%% ===================== METRIC 1: TEMPO =====================
% m1a - Sampling
newfig(1100, 520);
t = (0:numel(wave)-1)/sr + wave_t0;
subplot(2,1,1); plot(t, wave, 'Color', cA); hold on; vline(0, [-1 1], 'k-', ink);
xlim([t(1) t(end)]); ylim([-1 1]); box off; set(gca,'FontSize',fs);
xlabel(sprintf('Time relative to exit point %s (s)', mmss(tA))); ylabel('Amplitude');
title(sprintf('Sampling: %s decoded at fs = %d Hz (4 s shown)', songA, sr), 'FontWeight','normal');
subplot(2,1,2);
z = find(t >= 0, 1); idx = z:z+109; ts = (idx - z)/sr*1000;
stem(ts, wave(idx), 'filled', 'Color', cA, 'MarkerSize', 3); hold on; plot(ts, wave(idx), ':', 'Color', gry);
xlim([0 ts(end)]); box off; set(gca,'FontSize',fs); xlabel('Time (ms)'); ylabel('Amplitude');
title(sprintf('Zoom: 110 samples = 5 ms, Ts = 1/fs = %.1f \\mus. Analysis frames advance %d samples (%.1f ms)', 1e6/sr, hop, 1000*hop/sr), 'FontWeight','normal');
save_png('m1a_sampling.png');

% m1b - STFT
newfig(1100, 460);
imagesc(spec_t, spec_f, spec); axis xy; colormap(gca, ramp(cA)); hold on;
mx = max(spec(:)); caxis([mx-70 mx]); cb = colorbar; ylabel(cb, 'dB');
vline(0, [0 5000], 'k--', ink); set(gca,'FontSize',fs);
xlabel(sprintf('Time relative to exit %s (s)', mmss(tA))); ylabel('Frequency (Hz)');
title(sprintf('Frequency domain: STFT, %d-point Hann window, hop %d (%s, 0-5 kHz)', nfft, hop, songA), 'FontWeight','normal');
save_png('m1b_stft.png');

% m1c - Spectral flux + comb-filter beat grid
newfig(1100, 520);
E = {envA, envA_t, beatsA, downA, cA, songA; envB, envB_t, beatsB, downB, cB, songB};
for k = 1:2
    subplot(2,1,k); hold on;
    for b = E{k,3}, vline(b, [0 1.05], ':', gry); end
    for b = E{k,4}, vline(b, [0 1.05], '-', ink); end
    area(E{k,2}, max(E{k,1}, 0) / max(E{k,1}), 'FaceColor', E{k,5}, 'EdgeColor', 'none');
    xlim([-4 4]); ylim([0 1.05]); box off; set(gca,'FontSize',fs); ylabel('Onset strength');
    if k == 1
        title('Spectral-flux onset envelope with comb-filter beat grid: dotted = beat, solid = downbeat', 'FontWeight','normal');
    else
        xlabel('Time relative to the cut point (s)');
    end
    text(-3.9, 0.98, E{k,6}, 'FontSize', 10, 'VerticalAlignment', 'top', 'BackgroundColor', 'w');
end
save_png('m1c_flux_beats.png');

% m1d - Fourier tempogram
newfig(1100, 440); hold on;
zb = [bpmA*0.92 min(200, bpmA*1.08)];
fill([zb(1) zb(2) zb(2) zb(1)], [0 0 1.08 1.08], cX, 'EdgeColor', 'none');
hA = plot(tempo_bpm, tempo_A, 'Color', cA, 'LineWidth', 1.6); hB = plot(tempo_bpm, tempo_B, 'Color', cB, 'LineWidth', 1.6);
[~, iA] = max(tempo_A); [~, iB] = max(tempo_B);
plot(tempo_bpm(iA), tempo_A(iA), 'o', 'MarkerFaceColor', cA, 'MarkerEdgeColor', 'w', 'MarkerSize', 7);
plot(tempo_bpm(iB), tempo_B(iB), 'o', 'MarkerFaceColor', cB, 'MarkerEdgeColor', 'w', 'MarkerSize', 7);
text(zb(1)-2, 0.85, '\pm8% stretch zone', 'HorizontalAlignment', 'right', 'FontSize', 10);
xlim([60 200]); ylim([0 1.08]); box off; set(gca,'FontSize',fs); xlabel('Tempo (BPM)'); ylabel('|DFT| (normalized)');
legend([hA hB], {sprintf('%s  %.1f BPM', songA, bpmA), sprintf('%s  %.1f BPM', songB, bpmB)}, 'Location','northwest'); legend boxoff;
title(sprintf('Frequency domain: Fourier tempogram = DFT of the onset envelope, frequency = BPM/60  |  tempo adds +%.2f of %.2f', weights(1)*scores(1), weights(1)), 'FontWeight','normal');
save_png('m1d_tempogram.png');

%% ===================== METRIC 2: KEY =====================
% m2a - one frame's spectrum with tonal peaks, coloured by pitch class
newfig(1100, 440);
semilogx(frame_f, frame_mag, 'Color', gry); hold on;
pcc = hsv(12);
[~, ord] = sort(frame_mag(frame_pk), 'descend');
for j = 1:numel(frame_pk)
    i = frame_pk(j); c = pcc(frame_pc(i)+1, :);
    plot(frame_f(i), frame_mag(i), 'o', 'MarkerFaceColor', c, 'MarkerEdgeColor', 'k', 'MarkerSize', 6);
end
for j = reshape(ord(1:min(8, numel(ord))), 1, [])
    i = frame_pk(j); text(frame_f(i), frame_mag(i)+3, notes{frame_pc(i)+1}, 'HorizontalAlignment','center', 'FontSize', 10);
end
set(gca, 'XScale', 'log', 'FontSize', fs); xlim([65 2100]); box off; xlabel('Frequency (Hz)'); ylabel('Magnitude (dB)');
title(sprintf('Spectral peak picking: one STFT frame of %s at %s; dots = tonal peaks (> 4x local median), colour = pitch class', songA, mmss(tA)), 'FontWeight','normal');
save_png('m2a_peaks.png');

% m2b - chromagram (change of basis)
newfig(1100, 560);
C = {chromA, songA, tA, cA; chromB, songB, tB, cB};
for k = 1:2
    subplot(2,1,k);
    tc = (0:size(C{k,1},2)-1) * blk_sec;
    imagesc(tc, 1:12, C{k,1}); axis xy; colormap(gca, ramp(C{k,4})); hold on;
    vline(C{k,3}, [0.5 12.5], 'k-', ink);
    set(gca, 'YTick', 1:12, 'YTickLabel', notes, 'FontSize', 9); ylabel(C{k,2});
    if k == 1
        title('Processing in a different basis: STFT bins 65-2100 Hz mapped to 12 pitch classes, pc = round(12 log2(f/440) + 69) mod 12', 'FontWeight','normal');
    else
        xlabel('Time (s); black line = cut point');
    end
end
save_png('m2b_chromagram.png');

% m2c - Krumhansl-Schmuckler key profiles
newfig(1100, 520);
K = {kcA, songA, keyA, cA; kcB, songB, keyB, cB};
lab = [notes, cellfun(@(s) [lower(s) 'm'], notes, 'UniformOutput', false)];
for k = 1:2
    subplot(2,1,k);
    v = [K{k,1}(1,:) K{k,1}(2,:)]; [vb, ib] = max(v);
    b = bar(1:24, v, 'FaceColor', K{k,4}, 'EdgeColor', 'none'); hold on;
    bar(ib, vb, 'FaceColor', ink, 'EdgeColor', 'none');
    plot([12.5 12.5], [-1 1], ':', 'Color', gry);
    set(gca, 'XTick', 1:24, 'XTickLabel', lab, 'FontSize', 8); xlim([0.4 24.6]); ylim([-1 1]); box off; ylabel('Correlation r');
    text(0.8, 0.85, sprintf('%s: best = %s (r = %.2f)   |   major keys left, minor keys right', K{k,2}, K{k,3}, vb), 'FontSize', 10);
    if k == 1, title('Krumhansl-Schmuckler key profiles: mean chroma correlated with 24 major/minor templates', 'FontWeight','normal'); end
end
save_png('m2c_key_profiles.png');

% m2d - circular-shift search
newfig(1100, 440); hold on;
sh = -6:5; sv = sims(mod(sh, 12) + 1);
fill([-2.5 2.5 2.5 -2.5], [0 0 1.05 1.05], cX, 'EdgeColor', 'none');
stem(sh, sv, 'filled', 'Color', cB, 'LineWidth', 1.5);
pen = sv - 0.03*abs(sh); in = abs(sh) <= 2;
plot(sh(in), pen(in), 'kd', 'MarkerFaceColor', 'w', 'MarkerSize', 7);
plot(shift, sims(mod(shift,12)+1), 'o', 'MarkerEdgeColor', ink, 'MarkerSize', 16, 'LineWidth', 2);
set(gca, 'XTick', sh, 'FontSize', fs); xlim([-6.5 5.5]); ylim([0 1.05]); box off;
xlabel(sprintf('Semitones %s is shifted (circular rotation of its chroma vector)', songB)); ylabel('Correlation with A');
legend({'allowed shifts (\pm2)', 'raw correlation', 'after 0.03/semitone penalty', sprintf('chosen: %+d', shift)}, 'Location', 'northeastoutside'); legend boxoff;
title(sprintf('Circular-shift search: rotate B''s chroma and correlate with A  |  key adds +%.2f of %.2f', weights(2)*scores(2), weights(2)), 'FontWeight','normal');
save_png('m2d_shift_search.png');

%% ===================== METRIC 3: SPECTRUM / FILTERS =====================
% m3a - band energy
newfig(1100, 440);
names = cell(1, numel(bandA));
for k = 1:numel(bandA), names{k} = sprintf('%g-%g Hz', band_edges(k), band_edges(k+1)); end
b = barh(1:numel(bandA), 100*[bandA(:) bandB(:)], 'grouped', 'EdgeColor', 'none');
set(b(1), 'FaceColor', cA); set(b(2), 'FaceColor', cB);
set(gca, 'YTick', 1:numel(bandA), 'YTickLabel', names, 'YDir', 'reverse', 'FontSize', fs); box off;
xlabel('Share of total energy (%)'); legend({songA, songB}, 'Location', 'southeast'); legend boxoff;
title(sprintf('Frequency domain: STFT power summed into 8 bands. Bass (<250 Hz) overlap = %.0f%% before filtering', 100*raw_clash), 'FontWeight','normal');
save_png('m3a_band_energy.png');

% m3b - magnitude and phase response
newfig(1100, 600);
subplot(2,1,1);
semilogx(wf, 20*log10(Hl), 'Color', cA, 'LineWidth', 1.8); hold on;
semilogx(wf, 20*log10(Hh), 'Color', cB, 'LineWidth', 1.8);
semilogx(wf, 40*log10(Hl), '--', 'Color', cA); semilogx(wf, 40*log10(Hh), '--', 'Color', cB);
plot([400 400], [-80 5], 'k:'); plot([10 sr/2], [-3 -3], ':', 'Color', gry);
set(gca, 'XScale', 'log', 'FontSize', fs); xlim([10 sr/2]); ylim([-80 5]); box off; ylabel('|H(f)| (dB)');
legend({'Low-pass, one pass', 'High-pass, one pass', 'LP forward+backward (filtfilt)', 'HP forward+backward'}, 'Location', 'southwest'); legend boxoff;
title('Studying system properties: 4th-order Butterworth at 400 Hz. -3 dB at cutoff, 24 dB/octave roll-off (48 with filtfilt)', 'FontWeight','normal');
subplot(2,1,2);
semilogx(wf, phl*180/pi, 'Color', cA, 'LineWidth', 1.8); hold on; semilogx(wf, phh*180/pi, 'Color', cB, 'LineWidth', 1.8);
semilogx(wf, 0*wf, 'k--', 'LineWidth', 1.4); plot([400 400], [-400 400], 'k:');
set(gca, 'XScale', 'log', 'FontSize', fs); xlim([10 sr/2]); box off; xlabel('Frequency (Hz)'); ylabel('Phase (degrees)');
legend({'LP phase, one pass', 'HP phase, one pass', 'filtfilt: zero phase (used here)'}, 'Location', 'southwest'); legend boxoff;
title('Phase: one pass shifts the bass in time (LP and HP curves overlap; they differ by exactly 360 deg). Forward+backward cancels it', 'FontWeight','normal');
save_png('m3b_freq_phase_response.png');

% m3c - pole-zero plot
newfig(1100, 480);
th = linspace(0, 2*pi, 400);
for k = 1:2
    subplot(1,2,k); hold on;
    plot(cos(th), sin(th), 'Color', gry); plot([-1.2 1.2], [0 0], ':', 'Color', gry); plot([0 0], [-1.2 1.2], ':', 'Color', gry);
    plot(p_lp(:,1), p_lp(:,2), 'x', 'Color', cA, 'MarkerSize', 11, 'LineWidth', 2);
    plot(z_lp(:,1), z_lp(:,2), 'o', 'Color', cA, 'MarkerSize', 10, 'LineWidth', 1.5);
    plot(p_hp(:,1), p_hp(:,2), 'x', 'Color', cB, 'MarkerSize', 11, 'LineWidth', 2);
    plot(z_hp(:,1), z_hp(:,2), 'o', 'Color', cB, 'MarkerSize', 10, 'LineWidth', 1.5);
    axis equal; box off; set(gca, 'FontSize', fs); xlabel('Re(z)'); ylabel('Im(z)');
    if k == 1
        xlim([-1.2 1.2]); ylim([-1.2 1.2]);
        title('Pole-zero plot (z-plane): both filters share the same 4 poles (x); only the zeros (o) differ', 'FontWeight','normal');
        text(-1.15, 1.1, 'blue = low-pass (zeros at z = -1), orange = high-pass (zeros at z = +1)', 'FontSize', 9);
    else
        xlim([0.75 1.05]); ylim([-0.15 0.15]);
        title(sprintf('Zoom near z = 1: max |pole| = %.4f < 1, so both filters are stable', max(hypot(p_lp(:,1), p_lp(:,2)))), 'FontWeight','normal');
    end
end
save_png('m3c_pole_zero.png');

% m3d - impulse and step response
newfig(1100, 420);
tm = (0:numel(h_lp)-1)/sr*1000;
subplot(1,2,1); plot(tm, h_lp, 'Color', cA, 'LineWidth', 1.6); box off; set(gca,'FontSize',fs);
xlabel('Time (ms)'); ylabel('h[n]'); title('Linear systems: impulse response h[n] of the low-pass', 'FontWeight','normal');
subplot(1,2,2); plot(tm, s_lp, 'Color', cA, 'LineWidth', 1.6); hold on; plot(tm, ones(size(tm)), ':', 'Color', gry);
box off; set(gca,'FontSize',fs); xlabel('Time (ms)'); ylabel('Output');
title('Step response = running sum of h[n]: settles to 1 within a few ms', 'FontWeight','normal');
save_png('m3d_impulse_step.png');

% m3e - bass handoff ramp (convolution) and equal-power gains
newfig(1100, 560);
subplot(2,1,1); hold on;
plot(ramp_t, stepA, ':', 'Color', cA, 'LineWidth', 1.4); plot(ramp_t, 1-stepA, ':', 'Color', cB, 'LineWidth', 1.4);
plot(ramp_t, rampA, 'Color', cA, 'LineWidth', 2); plot(ramp_t, 1-rampA, 'Color', cB, 'LineWidth', 2);
xlim([0 xf]); ylim([-0.05 1.05]); box off; set(gca,'FontSize',fs); ylabel('Bass gain');
legend({'A bass, hard step', 'B bass, hard step', 'A bass = step * 250 ms boxcar', 'B bass = 1 - A'}, 'Location', 'east'); legend boxoff;
title(sprintf('Linear systems: the bass swap is a step convolved with a 250 ms boxcar, a smooth ramp at %.1f s', xf/2), 'FontWeight','normal');
subplot(2,1,2); hold on; u = ramp_t/xf;
plot(ramp_t, cos(pi/2*u), 'Color', cA, 'LineWidth', 2); plot(ramp_t, sin(pi/2*u), 'Color', cB, 'LineWidth', 2);
plot(ramp_t, cos(pi/2*u).^2 + sin(pi/2*u).^2, 'k--');
xlim([0 xf]); ylim([0 1.1]); box off; set(gca,'FontSize',fs); xlabel('Time into crossfade (s)'); ylabel('Gain');
legend({'g_A = cos(\pi t/2)', 'g_B = sin(\pi t/2)', 'g_A^2 + g_B^2 = 1 (constant power)'}, 'Location', 'east'); legend boxoff;
title(sprintf('Equal-power crossfade  |  spectrum adds +%.2f of %.2f (clash %.0f%% -> %.1f%%)', weights(3)*scores(3), weights(3), 100*raw_clash, 100*post_clash), 'FontWeight','normal');
save_png('m3e_handoff_ramp.png');

%% ===================== METRIC 4: ENERGY / STRUCTURE =====================
% m4a - framed RMS loudness
newfig(1100, 520);
R = {rmsA, songA, tA, cA; rmsB, songB, tB, cB};
for k = 1:2
    subplot(2,1,k); tr = (0:numel(R{k,1})-1)*rms_step;
    area(tr, max(R{k,1}, -50), -50, 'FaceColor', R{k,4}, 'EdgeColor', 'none'); hold on;
    vline(R{k,3}, [-50 0], 'k-', ink);
    xlim([0 tr(end)]); ylim([-50 0]); box off; set(gca,'FontSize',fs); ylabel([R{k,2} ' (dB)']);
    if k == 1
        title(sprintf('Sampling / framing: RMS of 2048-sample windows every %d samples, in dB; black = cut point', hop), 'FontWeight','normal');
    else
        xlabel('Time (s)');
    end
end
save_png('m4a_loudness.png');

% m4b - self-similarity matrices
newfig(1100, 520);
S = {ssmA, tA, cA, songA; ssmB, tB, cB, songB};
for k = 1:2
    subplot(1,2,k); M = S{k,1}; n = size(M,1); ts2 = (0:n-1)*blk_sec;
    imagesc(ts2, ts2, M, [-.2 1]); axis image; hold on; colormap(gca, ramp(S{k,3}));
    plot([S{k,2} S{k,2}], [0 ts2(end)], 'k', 'LineWidth', 1.2); plot([0 ts2(end)], [S{k,2} S{k,2}], 'k', 'LineWidth', 1.2);
    set(gca,'FontSize',fs); xlabel('Time (s)');
    title(sprintf('%s: cosine similarity of every 1 s block pair', S{k,4}), 'FontWeight','normal');
end
save_png('m4b_ssm.png');

% m4c - checkerboard kernel
newfig(1100, 460);
subplot(1,2,1); imagesc(kern, [-1 1]); axis image; colormap(gca, div); colorbar; set(gca,'FontSize',fs);
title('Image processing: 16x16 checkerboard kernel', 'FontWeight','normal');
subplot(1,2,2); mesh(kern); colormap(gca, div); set(gca,'FontSize',fs); view(-35, 35); zlim([-1 1]);
title('Same kernel in 3D: + quadrants = within-section, - = across', 'FontWeight','normal');
save_png('m4c_kernel.png');

% m4d - novelty curve
newfig(1100, 520);
N = {nvA, pkA, tA, cA, songA; nvB, pkB, tB, cB, songB};
for k = 1:2
    subplot(2,1,k); tn = (0:numel(N{k,1})-1)*blk_sec;
    area(tn, N{k,1}, 'FaceColor', N{k,4}, 'EdgeColor', 'none'); hold on;
    plot(tn(N{k,2}), N{k,1}(N{k,2}), 'kv', 'MarkerFaceColor', 'w', 'MarkerSize', 7);
    vline(N{k,3}, [0 1.05], 'k-', ink);
    xlim([0 tn(end)]); ylim([0 1.05]); box off; set(gca,'FontSize',fs); ylabel([N{k,5} ' novelty']);
    if k == 1
        title(sprintf('Kernel convolved along the SSM diagonal = novelty curve; triangles = section boundaries  |  structure adds +%.2f of %.2f', weights(4)*scores(4), weights(4)), 'FontWeight','normal');
    else
        xlabel('Time (s); black = cut point');
    end
end
save_png('m4d_novelty.png');

%% ===================== COMPARISON AND OUTPUT =====================
% c1 - cross-correlation for beat alignment
newfig(1100, 420);
plot(xc_lag, xc, 'Color', ink, 'LineWidth', 1.6); hold on;
[mxc, im] = max(xc); plot(xc_lag(im), mxc, 'o', 'MarkerFaceColor', cB, 'MarkerEdgeColor', 'w', 'MarkerSize', 10);
plot([0 0], [min(xc) 1.05], ':', 'Color', gry); ylim([min(0, min(xc)) 1.1]);
box off; set(gca,'FontSize',fs); xlabel(sprintf('Lag applied to %s (ms)', songB)); ylabel('Normalized cross-correlation');
title(sprintf('Linear systems: cross-correlation of the two onset envelopes over the fade. Peak at %.0f ms = beat-alignment offset', xc_lag(im)), 'FontWeight','normal');
save_png('c1_xcorr.png');

% c2 - A x B cross-similarity
newfig(900, 700);
tAx = (0:size(X,1)-1)*blk_sec; tBx = (0:size(X,2)-1)*blk_sec;
imagesc(tBx, tAx, X, [-.2 1]); hold on; colormap(gca, ramp(cA)); colorbar;
plot(cands(2:end,2), cands(2:end,1), 'o', 'MarkerFaceColor', ink, 'MarkerEdgeColor', 'w', 'MarkerSize', 6);
plot(cands(1,2), cands(1,1), 'o', 'MarkerEdgeColor', ink, 'LineWidth', 2, 'MarkerSize', 14);
set(gca,'FontSize',fs); xlabel([songB ' time (s)']); ylabel([songA ' time (s)']);
title(sprintf('Comparison: A x B cross-similarity + weighted grid search. Best %s -> %s (%.3f)', mmss(cands(1,1)), mmss(cands(1,2)), cands(1,5)), 'FontWeight','normal');
save_png('c2_crosssim.png');

% c3 - output spectrogram
newfig(1100, 460);
nt = size(mix_spec,2); nfq = size(mix_spec,1);
imagesc(linspace(0, xf, nt), linspace(0, 5000, nfq), mix_spec, [.3 1]); axis xy; hold on; colormap(gca, ramp(cA));
uu = linspace(0,1,200);
plot(uu*xf, 4800*cos(pi/2*uu), 'Color', cA, 'LineWidth', 2.2); plot(uu*xf, 4800*sin(pi/2*uu), 'Color', cB, 'LineWidth', 2.2);
plot([0 xf], [400 400], 'k--'); plot([xf/2 xf/2], [0 5000], 'k--');
set(gca,'FontSize',fs); xlabel('Time into crossfade (s)'); ylabel('Frequency (Hz)');
legend({'g_A', 'g_B'}, 'Location', 'east');
title(sprintf('Output check, frequency domain: STFT of the rendered %.1f s crossfade; bass passes from A to B at %.1f s', xf, xf/2), 'FontWeight','normal');
save_png('c3_output.png');

% c4 - weighted score
newfig(1100, 300); hold on;
contrib = weights(:)' .* scores(:)'; cols = [cA; cB; cG; cY];
labels = {'Tempo', 'Key', 'Spectral', sprintf('Energy/\nstructure')}; left = 0;
for k = 1:4
    rectangle('Position', [left 0 contrib(k) 1], 'FaceColor', cols(k,:), 'EdgeColor', 'w', 'LineWidth', 2);
    if contrib(k) > .07
        text(left + contrib(k)/2, .5, sprintf('%s\n+%.2f', labels{k}, contrib(k)), 'HorizontalAlignment', 'center', 'FontSize', 10);
    else
        text(left + contrib(k)/2, 1.08, sprintf('%s +%.2f', strrep(labels{k}, sprintf('\n'), ''), contrib(k)), 'HorizontalAlignment', 'center', 'FontSize', 9);
    end
    left = left + contrib(k);
end
rectangle('Position', [left 0 1-left 1], 'FaceColor', [.93 .93 .92], 'EdgeColor', 'w', 'LineWidth', 2);
text(left + (1-left)/2, .5, sprintf('lost\n-%.2f', 1-left), 'HorizontalAlignment', 'center', 'FontSize', 10, 'Color', [.4 .4 .4]);
xlim([0 1]); ylim([0 1.18]); set(gca, 'YTick', [], 'FontSize', fs); xlabel('Score (0 to 1)');
title(sprintf('Weighted score: %.2f = 0.35 tempo + 0.30 key + 0.20 spectral + 0.15 energy', total), 'FontWeight','normal');
save_png('c4_score.png');

disp('Saved 21 figures to ./figures');
