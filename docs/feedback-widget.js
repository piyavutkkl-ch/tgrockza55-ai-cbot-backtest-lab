/**
 * ANTIGRAVITY QUANT - In-Page Visual Crop Feedback Widget
 * Allows cropping any part of the active page, writing comments,
 * and generating ready-to-paste AI directives.
 */
(function() {
  // Ensure html2canvas is loaded
  if (typeof html2canvas === 'undefined') {
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
    document.head.appendChild(s);
  }

  const STORAGE_KEY = 'agq_feedback_tasks';

  // Inject styles
  const style = document.createElement('style');
  style.textContent = `
    .agq-crop-btn {
      position: fixed;
      bottom: 64px;
      right: 16px;
      z-index: 9998;
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: 999px;
      background: linear-gradient(135deg, #e11d48, #f59e0b);
      color: #ffffff;
      font-family: 'Plus Jakarta Sans', 'Noto Sans Thai', sans-serif;
      font-size: 13px;
      font-weight: 800;
      box-shadow: 0 8px 24px rgba(225, 29, 72, 0.45);
      border: 1px solid rgba(255, 255, 255, 0.25);
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .agq-crop-btn:hover {
      transform: translateY(-2px) scale(1.05);
      box-shadow: 0 12px 28px rgba(225, 29, 72, 0.6);
    }
    .agq-crop-overlay {
      position: fixed;
      inset: 0;
      z-index: 99999;
      background: rgba(0, 0, 0, 0.45);
      cursor: crosshair !important;
      user-select: none;
    }
    .agq-crop-box {
      position: absolute;
      border: 2px dashed #06b6d4;
      background: rgba(6, 182, 212, 0.15);
      border-radius: 6px;
      box-shadow: 0 0 20px rgba(6, 182, 212, 0.5);
      pointer-events: none;
    }
    .agq-crop-modal {
      position: fixed;
      inset: 0;
      z-index: 100000;
      background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      font-family: 'Plus Jakarta Sans', 'Noto Sans Thai', sans-serif;
    }
    .agq-modal-card {
      background: #0b111e;
      border: 2px solid rgba(244, 63, 94, 0.6);
      border-radius: 20px;
      max-width: 540px;
      width: 100%;
      padding: 20px;
      color: #e2e8f0;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8);
    }
    .agq-toast {
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 100001;
      background: #0f172a;
      border: 2px solid #10b981;
      color: #fff;
      padding: 10px 20px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
      display: flex;
      align-items: center;
      gap: 8px;
    }
  `;
  document.head.appendChild(style);

  // Create Floating Action Button
  const btn = document.createElement('button');
  btn.className = 'agq-crop-btn';
  btn.innerHTML = `<span>✂️</span><span>Crop แก้ไข AI</span>`;
  btn.title = 'คลิกเพื่อลาก Crop จุดที่ต้องการให้ AI แก้ไขบนหน้านี้';
  btn.onclick = showInPageMenu;
  document.body.appendChild(btn);

  function showInPageMenu() {
    const existing = document.getElementById('agq-quick-menu');
    if (existing) { existing.remove(); return; }

    const menu = document.createElement('div');
    menu.id = 'agq-quick-menu';
    menu.style.cssText = `
      position: fixed;
      bottom: 110px;
      right: 16px;
      z-index: 9999;
      background: #0b111e;
      border: 1px solid #334155;
      border-radius: 16px;
      padding: 8px;
      box-shadow: 0 12px 32px rgba(0,0,0,0.7);
      width: 220px;
      font-family: 'Plus Jakarta Sans', 'Noto Sans Thai', sans-serif;
      font-size: 12px;
    `;

    menu.innerHTML = `
      <div style="font-weight: 800; color: #f43f5e; padding: 6px 8px; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center;">
        <span>📸 VISUAL FEEDBACK</span>
        <button onclick="document.getElementById('agq-quick-menu').remove()" style="background:none; border:none; color:#64748b; cursor:pointer; font-size:12px;">✕</button>
      </div>
      <button id="agq-btn-instant-crop" style="width: 100%; text-align: left; padding: 10px; border-radius: 10px; background: rgba(244, 63, 94, 0.15); color: #f43f5e; font-weight: 700; border: 1px solid rgba(244, 63, 94, 0.3); margin-top: 6px; cursor: pointer;">
        ✂️ Crop บนหน้านี้ทันที
      </button>
      <a href="feedback.html" style="display: block; width: 100%; text-align: left; padding: 10px; border-radius: 10px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-weight: 700; border: 1px solid rgba(56, 189, 248, 0.3); margin-top: 6px; text-decoration: none; box-sizing: border-box;">
        🖥️ เปิดในสตูดิโอเต็มหน้า
      </a>
    `;

    document.body.appendChild(menu);

    document.getElementById('agq-btn-instant-crop').onclick = () => {
      menu.remove();
      startInPageCrop();
    };

    // Close on outside click
    setTimeout(() => {
      window.addEventListener('click', function closeMenu(e) {
        if (!e.target.closest('#agq-quick-menu') && e.target !== btn) {
          menu.remove();
          window.removeEventListener('click', closeMenu);
        }
      });
    }, 50);
  }

  // Instant in-page cropping
  async function startInPageCrop() {
    showToast('⏳ กำลังเตรียมพื้นที่หน้าจอ...', '⏱️');

    // Screenshot page with html2canvas if available
    let screenshotCanvas = null;
    try {
      if (typeof html2canvas !== 'undefined') {
        screenshotCanvas = await html2canvas(document.body, {
          useCORS: true,
          logging: false,
          windowWidth: window.innerWidth,
          windowHeight: window.innerHeight,
          x: window.scrollX,
          y: window.scrollY,
          width: window.innerWidth,
          height: window.innerHeight
        });
      }
    } catch (e) {}

    const overlay = document.createElement('div');
    overlay.className = 'agq-crop-overlay';

    const guide = document.createElement('div');
    guide.style.cssText = `
      position: absolute;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: #0f172a;
      border: 2px solid #f43f5e;
      color: #fff;
      padding: 8px 18px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 800;
      box-shadow: 0 10px 30px rgba(0,0,0,0.8);
      pointer-events: none;
    `;
    guide.textContent = '✂️ คลิกเมาส์ค้างแล้วลากครอบบริเวณที่ต้องการแจ้ง AI (ESC เพื่อยกเลิก)';
    overlay.appendChild(guide);

    const box = document.createElement('div');
    box.className = 'agq-crop-box';
    box.style.display = 'none';
    overlay.appendChild(box);

    let isDown = false;
    let sX = 0, sY = 0, cX = 0, cY = 0, cW = 0, cH = 0;

    overlay.onmousedown = (e) => {
      isDown = true;
      sX = e.clientX;
      sY = e.clientY;
      box.style.left = sX + 'px';
      box.style.top = sY + 'px';
      box.style.width = '0px';
      box.style.height = '0px';
      box.style.display = 'block';
    };

    overlay.onmousemove = (e) => {
      if (!isDown) return;
      cX = Math.min(sX, e.clientX);
      cY = Math.min(sY, e.clientY);
      cW = Math.abs(e.clientX - sX);
      cH = Math.abs(e.clientY - sY);
      box.style.left = cX + 'px';
      box.style.top = cY + 'px';
      box.style.width = cW + 'px';
      box.style.height = cH + 'px';
    };

    overlay.onmouseup = () => {
      if (!isDown) return;
      isDown = false;
      if (cW > 25 && cH > 25) {
        overlay.remove();
        processCropResult(screenshotCanvas, cX, cY, cW, cH);
      }
    };

    window.addEventListener('keydown', function escCancel(e) {
      if (e.key === 'Escape') {
        overlay.remove();
        window.removeEventListener('keydown', escCancel);
      }
    });

    document.body.appendChild(overlay);
  }

  function processCropResult(sourceCanvas, x, y, w, h) {
    let croppedDataUrl = '';
    const cropCanvas = document.createElement('canvas');
    cropCanvas.width = w;
    cropCanvas.height = h;
    const ctx = cropCanvas.getContext('2d');

    if (sourceCanvas) {
      ctx.drawImage(sourceCanvas, x, y, w, h, 0, 0, w, h);
      croppedDataUrl = cropCanvas.toDataURL('image/png');
    } else {
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = '#f43f5e';
      ctx.lineWidth = 3;
      ctx.strokeRect(0, 0, w, h);
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 12px sans-serif';
      ctx.fillText(`Crop: ${w}x${h}px`, 15, 25);
      croppedDataUrl = cropCanvas.toDataURL('image/png');
    }

    showCommentModal(croppedDataUrl, { x, y, w, h });
  }

  function showCommentModal(croppedDataUrl, coords) {
    const pageName = location.pathname.split('/').pop() || 'index.html';

    const modal = document.createElement('div');
    modal.className = 'agq-crop-modal';

    modal.innerHTML = `
      <div class="agq-modal-card">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; padding-bottom:12px; margin-bottom:14px;">
          <div>
            <div style="font-weight:800; font-size:16px; color:#fff;">✂️ ระบุสิ่งที่ต้องการให้ AI แก้ไขตรงนี้</div>
            <div style="font-size:11px; color:#94a3b8; font-family:monospace; margin-top:2px;">หน้า: ${pageName} (${coords.w}×${coords.h}px)</div>
          </div>
          <button id="agq-close-modal" style="background:#1e293b; border:none; color:#cbd5e1; border-radius:8px; width:28px; height:28px; cursor:pointer;">✕</button>
        </div>

        <div style="text-align:center; background:#020617; border-radius:12px; padding:8px; margin-bottom:12px;">
          <img src="${croppedDataUrl}" style="max-height:160px; max-width:100%; border-radius:8px; object-fit:contain; border:1px solid #334155;">
        </div>

        <div style="margin-bottom:10px;">
          <label style="display:block; font-size:11px; font-weight:700; color:#cbd5e1; margin-bottom:4px;">1. ชื่อจุด / ส่วนประกอบ:</label>
          <input type="text" id="agq-comp-name" placeholder="เช่น แถบสถิติด้านบน, ปุ่ม Kill Switch, การ์ดบอท" style="width:100%; box-sizing:border-box; background:#020617; border:1px solid #334155; border-radius:8px; padding:8px; color:#fff; font-size:12px;">
        </div>

        <div style="margin-bottom:10px;">
          <label style="display:block; font-size:11px; font-weight:700; color:#cbd5e1; margin-bottom:4px;">2. คำสั่งสำหรับ AI (ระบุสิ่งที่ต้องการให้แก้):</label>
          <textarea id="agq-comment-text" rows="3" placeholder="เช่น อยากให้เปลี่ยนสีปุ่มเป็นสีเขียวมรกต, ขยายตัวเลขนี้ให้เด่นขึ้น, แก้ไขให้รองรับมือถือ..." style="width:100%; box-sizing:border-box; background:#020617; border:1px solid #334155; border-radius:8px; padding:8px; color:#fff; font-size:12px; line-height:1.4;"></textarea>
        </div>

        <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:14px; border-top:1px solid #1e293b; padding-top:12px;">
          <button id="agq-cancel-btn" style="padding:8px 14px; border-radius:8px; background:#1e293b; color:#cbd5e1; border:none; font-size:12px; font-weight:700; cursor:pointer;">ยกเลิก</button>
          <button id="agq-copy-btn" style="padding:8px 16px; border-radius:8px; background:linear-gradient(135deg, #10b981, #06b6d4); color:#020617; border:none; font-size:12px; font-weight:800; cursor:pointer; box-shadow:0 4px 12px rgba(16,185,129,0.3);">
            📋 คัดลอก Prompt สั่ง AI ทันที
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('agq-close-modal').onclick = () => modal.remove();
    document.getElementById('agq-cancel-btn').onclick = () => modal.remove();

    document.getElementById('agq-copy-btn').onclick = () => {
      const comp = document.getElementById('agq-comp-name').value.trim() || 'ส่วนประกอบที่เลือก';
      const comment = document.getElementById('agq-comment-text').value.trim() || 'ช่วยปรับปรุงส่วนนี้ให้สวยงามและถูกต้อง';

      const task = {
        id: 'TASK-' + String(Date.now()).slice(-4),
        page: pageName,
        component: comp,
        category: 'UI_DESIGN',
        priority: 'NORMAL',
        instruction: comment,
        coords: coords,
        imageUrl: croppedDataUrl,
        status: 'PENDING',
        created_at: new Date().toISOString()
      };

      // Save to localStorage
      try {
        let list = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        list.unshift(task);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
      } catch (e) {}

      // Generate Prompt for AI
      const prompt = `### 🛠️ [${task.id}] คำสั่งแก้ไขโค้ดจากหน้าเว็บ (Visual Crop Feedback)
- **หน้าเว็บเป้าหมาย**: \`${task.page}\`
- **องค์ประกอบ**: **${task.component}**
- **พิกัด Crop**: (x: ${coords.x}, y: ${coords.y}, ขนาด: ${coords.w}×${coords.h}px)
- **สิ่งที่ต้องการให้ AI แก้ไข**:
  > "${task.instruction}"
- **คำแนะนำสำหรับ AI**: ตรวจสอบไฟล์ \`${task.page}\` และแก้โค้ดให้ตรงตามคำสั่งนี้`;

      navigator.clipboard.writeText(prompt).then(() => {
        modal.remove();
        showToast('✅ คัดลอก Prompt แล้ว! วางในแชทให้ AI แก้ไขได้ทันที', '📋');
      });
    };
  }

  function showToast(text, icon = '✅') {
    const existing = document.querySelector('.agq-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'agq-toast';
    toast.innerHTML = `<span>${icon}</span><span>${text}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 2800);
  }

})();
