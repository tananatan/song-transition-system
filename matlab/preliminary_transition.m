%% EECS 351 Group 7: preliminary song-transition test
% Baseline only: not the finished beat-matching system.
clear; close all; clc;
use_demo = true;
clip_seconds = 12; fade_seconds = 4;
folder = fileparts(mfilename('fullpath'));
if isempty(folder), folder = pwd; end
out = fullfile(folder, 'results');
if ~exist(out, 'dir'), mkdir(out); end
if use_demo
 Fs=22050; t=(0:round(clip_seconds*Fs)-1)'/Fs;
 % Generated tones with decaying beat pulses, NOT real songs.
 pulseA=exp(-mod(t,60/120)/0.035);
 pulseB=exp(-mod(t,60/100)/0.035);
 a=.25*sin(2*pi*110*t)+.40*pulseA.*sin(2*pi*65*t);
 b=.25*sin(2*pi*165*t)+.40*pulseB.*sin(2*pi*85*t);
 nameA='Generated test A (120 BPM pulses)';
 nameB='Generated test B (100 BPM pulses)'; label='SYNTHETIC DEMO';
else
 [a,FsA]=audioread(fullfile(folder,'data','song_a.wav'));
 [b,FsB]=audioread(fullfile(folder,'data','song_b.wav'));
 if FsA~=FsB, error('Use clips with the same sample rate.'); end
 Fs=FsA; a=mean(a,2); b=mean(b,2);
 nameA='Audio clip A'; nameB='Audio clip B'; label='REAL AUDIO BASELINE';
end
N=min([length(a),length(b),round(clip_seconds*Fs)]);
a=a(1:N); b=b(1:N);
if N<2, error('Audio clips are too short.'); end
% Common peak scaling preserves relative amplitude, NOT loudness matching.
scale=max([max(abs(a)),max(abs(b)),eps]);
a=.9*a/scale; b=.9*b/scale; t=(0:N-1)'/Fs;
%% Plot 1: both input waveforms
figure('Color','w','Theme','light');
subplot(2,1,1); plot(t,a); grid on; ylim([-1 1]);
xlabel('Time (s)'); ylabel('Amplitude'); title(nameA);
subplot(2,1,2); plot(t,b); grid on; ylim([-1 1]);
xlabel('Time (s)'); ylabel('Amplitude'); title(nameB);
sgtitle([label ': input waveforms']);
print(gcf,fullfile(out,'plot1_waveforms.png'),'-dpng','-r180');
savefig(gcf,fullfile(out,'plot1_waveforms.fig'));
%% Plot 2: one-sided amplitude spectra, not PSD
w=.5-.5*cos(2*pi*(0:N-1)'/(N-1));
A=abs(fft(a.*w))/sum(w); B=abs(fft(b.*w))/sum(w);
K=floor(N/2)+1; A=A(1:K); B=B(1:K);
if mod(N,2)==0
 A(2:end-1)=2*A(2:end-1); B(2:end-1)=2*B(2:end-1);
else
 A(2:end)=2*A(2:end); B(2:end)=2*B(2:end);
end
f=(0:K-1)'*Fs/N;
figure('Color','w','Theme','light'); plot(f,20*log10(A+eps)); hold on;
plot(f,20*log10(B+eps)); grid on;
xlim([0 min(2000,Fs/2)]); ylim([-100 5]);
xlabel('Frequency (Hz)'); ylabel('Amplitude (dB re 1)');
legend('Clip A','Clip B'); title([label ': input spectra (first 2 kHz)']);
print(gcf,fullfile(out,'plot2_spectra.png'),'-dpng','-r180');
savefig(gcf,fullfile(out,'plot2_spectra.fig'));
%% Baseline linear crossfade
M=min(round(fade_seconds*Fs),N);
fade_out=linspace(1,0,M)'; fade_in=linspace(0,1,M)';
partA=a(end-M+1:end); partB=b(1:M);
overlap=fade_out.*partA+fade_in.*partB;
y=[a(1:end-M); overlap; b(M+1:end)];
start_fade=(N-M)/Fs; end_fade=(N-1)/Fs;
ty=(0:length(y)-1)'/Fs; tfade=start_fade+(0:M-1)'/Fs;
%% Plot 3: output and gains
figure('Color','w','Theme','light');
subplot(2,1,1); plot(ty,y); grid on; ylim([-1 1]);
xline(start_fade,'--'); xline(end_fade,'--');
xlabel('Time (s)'); ylabel('Amplitude');
title('Output waveform; dashed lines bound the overlap');
subplot(2,1,2); plot(tfade,fade_out); hold on; plot(tfade,fade_in); grid on;
xlabel('Time (s)'); ylabel('Gain'); legend('Clip A gain','Clip B gain');
title('Linear gains: one fades out while the other fades in');
sgtitle([label ': preliminary crossfade']);
print(gcf,fullfile(out,'plot3_crossfade.png'),'-dpng','-r180');
savefig(gcf,fullfile(out,'plot3_crossfade.fig'));
%% Save data and audio, no automatic playback
 audiowrite(fullfile(out,'input_a.wav'),a,Fs);
 audiowrite(fullfile(out,'input_b.wav'),b,Fs);
 audiowrite(fullfile(out,'crossfade.wav'),y,Fs);
 save(fullfile(out,'preliminary_results.mat'),'a','b','y','Fs','fade_out','fade_in','use_demo','nameA','nameB');
 fid=fopen(fullfile(out,'run_notes.txt'),'w');
 fprintf(fid,'%s\n',label);
 fprintf(fid,'Sample rate: %d Hz\nSamples per input: %d\n',Fs,N);
 fprintf(fid,'Input duration: %.4f s\nOverlap duration: %.4f s\n',N/Fs,M/Fs);
 fprintf(fid,'Output duration: %.4f s\nOutput peak: %.6f\n',length(y)/Fs,max(abs(y)));
 fprintf(fid,'No tempo adjustment, beat detection, pitch preservation or bass swap is implemented.\n');
 fclose(fid);
 fprintf('Saved three plots, audio, data and run notes to:\n%s\n',out);


