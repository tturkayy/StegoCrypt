import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { open, save } from '@tauri-apps/plugin-dialog';
import { openUrl } from '@tauri-apps/plugin-opener';
import { Lock, Unlock, Image as ImageIcon, FileText, Sparkles, Loader2, AlertTriangle } from 'lucide-react';

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0.0 KB';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  if (i === 0) return `${bytes} B`;
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export default function App() {
  const [tab, setTab] = useState('embed');
  const [coverPath, setCoverPath] = useState('');
  const [secretPath, setSecretPath] = useState('');
  const [stegoPath, setStegoPath] = useState('');
  const [password, setPassword] = useState('');

  const [bitDepth, setBitDepth] = useState(1);
  const [useUpscale, setUseUpscale] = useState(false);

  const [stats, setStats] = useState({ capacity_1bit: 0, capacity_2bit: 0, secret_size: 0 });
  const [quality, setQuality] = useState(null);
  const [status, setStatus] = useState({ text: 'System ready', type: 'idle' });
  const [isLoading, setIsLoading] = useState(false);

  // Disclaimer Onay Kontrolü
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);

  useEffect(() => {
    const accepted = localStorage.getItem('stegocrypt_disclaimer_accepted');
    if (accepted === 'true') {
      setDisclaimerAccepted(true);
    }
  }, []);

  const handleAcceptDisclaimer = () => {
    localStorage.setItem('stegocrypt_disclaimer_accepted', 'true');
    setDisclaimerAccepted(true);
  };

  useEffect(() => {
    if (coverPath) {
      setIsLoading(true);
      setStatus({ text: 'Analyzing image capacity...', type: 'loading' });
      invoke('analyze_capacity', { coverPath, secretPath: secretPath || '' })
        .then(res => {
          const parsed = JSON.parse(res);
          if (parsed.success) {
            setStats(parsed.data);
            setStatus({ text: 'Capacity calculated', type: 'idle' });
          } else {
            setStatus({ text: parsed.error, type: 'error' });
          }
        })
        .catch(err => {
          setStatus({ text: `Analysis error: ${err}`, type: 'error' });
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [coverPath, secretPath]);

  const selectCover = async () => {
    const file = await open({ filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg'] }] });
    if (file) setCoverPath(file);
  };

  const selectSecret = async () => {
    const file = await open({ multiple: false });
    if (file) setSecretPath(file);
  };

  const selectStego = async () => {
    const file = await open({ filters: [{ name: 'Stego PNG', extensions: ['png'] }] });
    if (file) setStegoPath(file);
  };

  const handleEmbed = async () => {
    if (!coverPath || !secretPath || !password) {
      setStatus({ text: 'Please select a cover image, secret file, and enter a password.', type: 'error' });
      return;
    }
    const outPath = await save({ filters: [{ name: 'Stego PNG', extensions: ['png'] }], defaultPath: 'stego_secured.png' });
    if (!outPath) return;

    setIsLoading(true);
    setStatus({ text: 'Compressing, encrypting, and embedding payload...', type: 'loading' });
    try {
      const res = await invoke('run_engine_embed', {
        coverPath, secretPath, outputPath: outPath, password, useUpscale, bitDepth
      });
      const parsed = JSON.parse(res);
      if (parsed.success) {
        setQuality({ psnr: parsed.data.psnr, ssim: parsed.data.ssim });
        setStatus({ text: `Success! Embedded Size: ${formatBytes(parsed.data.payload_size)}`, type: 'success' });
      } else {
        setStatus({ text: parsed.error, type: 'error' });
      }
    } catch (e) {
      setStatus({ text: `Error: ${e}`, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleExtract = async () => {
    if (!stegoPath || !password) {
      setStatus({ text: 'Please select a stego image and enter the password.', type: 'error' });
      return;
    }
    const outDir = await open({ directory: true });
    if (!outDir) return;

    setIsLoading(true);
    setStatus({ text: 'Decrypting and recovering payload...', type: 'loading' });
    try {
      const res = await invoke('run_engine_extract', { stegoPath, outputDir: outDir, password });
      const parsed = JSON.parse(res);
      if (parsed.success) {
        setStatus({ text: `File extracted: ${parsed.data.filename}`, type: 'success' });
      } else {
        setStatus({ text: parsed.error, type: 'error' });
      }
    } catch (e) {
      setStatus({ text: `Error: ${e}`, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const currentCapacity = (bitDepth === 1 ? stats.capacity_1bit : stats.capacity_2bit) * (useUpscale ? 4 : 1);
  const fillRatio = currentCapacity > 0 ? Math.min(100, Math.round((stats.secret_size / currentCapacity) * 100)) : 0;

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 antialiased font-sans select-none overflow-hidden relative">
      {/* Disclaimer Modal */}
      {!disclaimerAccepted && (
        <div className="absolute inset-0 z-50 bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 text-center">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 mx-auto flex items-center justify-center">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="space-y-2">
              <h2 className="text-lg font-bold tracking-wide text-slate-100">Terms of Use & Disclaimer</h2>
              <p className="text-xs text-slate-400 leading-relaxed text-left bg-slate-950/50 p-4 rounded-xl border border-slate-800 font-mono">
                This tool is designed for educational purposes and legitimate privacy protection only. The developer is not responsible for any misuse of this software for malicious activities.
              </p>
            </div>
            <button
              onClick={handleAcceptDisclaimer}
              className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 font-bold text-xs tracking-wider rounded-xl shadow-lg transition"
            >
              I AGREE & CONTINUE
            </button>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 p-6 flex flex-col justify-between">
        <div className="space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h1 className="font-extrabold tracking-widest text-lg text-slate-100">STEGOCRYPT</h1>
            <span className="text-xs text-emerald-400 font-mono tracking-wider">v2.0.0</span>
          </div>

          <nav className="space-y-2">
            <button
              onClick={() => setTab('embed')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition ${
                tab === 'embed'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'hover:bg-slate-800 text-slate-400'
              }`}
            >
              <Lock className="w-4 h-4" /> Encrypt & Hide
            </button>
            <button
              onClick={() => setTab('extract')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition ${
                tab === 'extract'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'hover:bg-slate-800 text-slate-400'
              }`}
            >
              <Unlock className="w-4 h-4" /> Decrypt & Extract
            </button>
          </nav>
        </div>

        <div className="text-xs text-slate-500 border-t border-slate-800 pt-4">
          Developed by{' '}
          <button
            onClick={() => openUrl('https://github.com/tturkayy')}
            className="text-emerald-400 hover:text-emerald-300 font-medium hover:underline focus:outline-none transition cursor-pointer"
          >
            Türkay Yıldırım
          </button>
        </div>
      </aside>

      {/* Main Panel */}
      <main className="flex-1 p-8 flex flex-col justify-between overflow-y-auto relative">
        <div className="space-y-6 max-w-4xl mx-auto w-full">
          {tab === 'embed' ? (
            <>
              <div className="grid grid-cols-2 gap-6">
                <div
                  onClick={selectCover}
                  className="border-2 border-dashed border-slate-800 hover:border-emerald-500/50 p-6 rounded-2xl bg-slate-900/40 flex flex-col items-center justify-center cursor-pointer transition"
                >
                  <ImageIcon className="w-8 h-8 text-emerald-400 mb-2" />
                  <p className="font-semibold text-sm">Cover Image</p>
                  <span className="text-xs text-slate-500 mt-1 truncate max-w-[200px]">
                    {coverPath ? coverPath.split('\\').pop() : 'Choose Image'}
                  </span>
                </div>

                <div
                  onClick={selectSecret}
                  className="border-2 border-dashed border-slate-800 hover:border-purple-500/50 p-6 rounded-2xl bg-slate-900/40 flex flex-col items-center justify-center cursor-pointer transition"
                >
                  <FileText className="w-8 h-8 text-purple-400 mb-2" />
                  <p className="font-semibold text-sm">Secret File</p>
                  <span className="text-xs text-slate-500 mt-1 truncate max-w-[200px]">
                    {secretPath ? secretPath.split('\\').pop() : 'Choose File'}
                  </span>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Capacity Usage ({fillRatio}%)</span>
                  <span>
                    {formatBytes(stats.secret_size)} / {formatBytes(currentCapacity)}
                  </span>
                </div>
                <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      fillRatio > 100 ? 'bg-red-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(fillRatio, 100)}%` }}
                  ></div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold">LSB Bit Depth:</span>
                  <div className="flex gap-2">
                    {[1, 2].map(d => (
                      <button
                        key={d}
                        onClick={() => setBitDepth(d)}
                        className={`px-3 py-1 rounded text-xs font-bold transition ${
                          bitDepth === d ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {d}-Bit
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" /> AI 2x Upscale:
                  </span>
                  <button
                    onClick={() => setUseUpscale(!useUpscale)}
                    className={`px-3 py-1 rounded text-xs font-bold transition ${
                      useUpscale ? 'bg-amber-600 text-white' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {useUpscale ? 'Active (4x Cap)' : 'Off'}
                  </button>
                </div>
              </div>

              <input
                type="password"
                placeholder="AES-256-GCM Password..."
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-emerald-500 font-mono transition"
              />

              {quality && (
                <div className="flex gap-4 p-3 bg-emerald-950/30 border border-emerald-500/20 rounded-xl text-xs font-mono text-emerald-400">
                  <span>PSNR: {quality.psnr} dB</span>
                  <span>•</span>
                  <span>SSIM: {quality.ssim}</span>
                </div>
              )}

              <button
                disabled={isLoading}
                onClick={handleEmbed}
                className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 font-bold rounded-xl shadow-lg transition flex items-center justify-center gap-2"
              >
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
                {isLoading ? 'PROCESSING...' : 'ENCRYPT & EMBED'}
              </button>
            </>
          ) : (
            <div className="space-y-6">
              <div
                onClick={selectStego}
                className="border-2 border-dashed border-slate-800 hover:border-emerald-500/50 p-10 rounded-2xl bg-slate-900/40 flex flex-col items-center justify-center cursor-pointer transition"
              >
                <ImageIcon className="w-10 h-10 text-emerald-400 mb-2" />
                <p className="font-semibold text-sm">Select Stego Image</p>
                <span className="text-xs text-slate-500 mt-1 truncate max-w-[300px]">
                  {stegoPath ? stegoPath.split('\\').pop() : 'No image selected'}
                </span>
              </div>

              <input
                type="password"
                placeholder="Decryption Password..."
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-emerald-500 font-mono transition"
              />

              <button
                disabled={isLoading}
                onClick={handleExtract}
                className="w-full py-4 bg-amber-600 hover:bg-amber-500 disabled:bg-slate-800 disabled:text-slate-500 font-bold rounded-xl shadow-lg transition flex items-center justify-center gap-2"
              >
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
                {isLoading ? 'PROCESSING...' : 'DECRYPT & EXTRACT FILE'}
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="border-t border-slate-800 pt-4 relative">
          {isLoading && (
            <div className="absolute top-0 left-0 w-full h-[2px] bg-slate-800 overflow-hidden">
              <div className="h-full bg-emerald-400 animate-indeterminate"></div>
            </div>
          )}
          <div className="flex justify-between items-center text-xs">
            <span className={`flex items-center gap-2 ${isLoading ? 'text-emerald-400' : 'text-slate-400'}`}>
              {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {status.text}
            </span>
            <span className="font-mono text-slate-500">{isLoading ? 'Working' : 'Ready'}</span>
          </div>
        </footer>
      </main>
    </div>
  );
}