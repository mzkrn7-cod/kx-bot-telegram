require("dotenv").config();

const allowedUsers = new Set();
const dataUser = {};

const OWNER_USERNAME = process.env.OWNER_USERNAME;
const BOT_TOKEN = process.env.BOT_TOKEN;

allowedUsers.add(OWNER_USERNAME.toLowerCase());

function hitungFee(saldo) {
  return Math.floor(saldo / 10) + 1;
}

function isAllowed(username) {
  if (!username) return false;

  username = username.toLowerCase();

  return (
    allowedUsers.has(username) ||
    username === OWNER_USERNAME.toLowerCase()
  );
}

function parseList(text) {
  const data = [];

  try {
    const lines = text.split("\n");

    for (let line of lines) {
      line = line.trim();

      if (!line || line.includes(":")) continue;

      const match = line.match(/(\d+)\s*(LF)?$/i);

      if (match) {
        const saldo = parseInt(match[1]);
        const lf = !!match[2];

        let nama = line.substring(0, match.index).trim();

        if (!nama) nama = "PLAYER";

        data.push({
          nama,
          saldo,
          lf,
        });
      }
    }
  } catch (e) {}

  return data;
}

async function sendMessage(chatId, text) {
  await fetch(
    `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        chat_id: chatId,
        text,
      }),
    }
  );
}

module.exports = async (req, res) => {
  try {
    const body = req.body;

    if (!body.message) {
      return res.status(200).send("ok");
    }

    const message = body.message;
    const chatId = message.chat.id;
    const text = message.text || "";
    const username = message.from.username;

    if (!isAllowed(username)) {
      return res.status(200).send("Unauthorized");
    }

    // =========================
    // SIMPAN LIST
    // =========================
    if (!text.startsWith("/") && text.includes(":")) {
      dataUser[chatId] = text;

      await sendMessage(chatId, "List disimpan ✅");

      return res.status(200).send("ok");
    }

    // =========================
    // START
    // =========================
    if (text === "/start") {
      await sendMessage(chatId, "Bot aktif ✅");

      return res.status(200).send("ok");
    }

    // =========================
    // ADD USER
    // =========================
    if (text.startsWith("/adduser")) {
      if (
        username.toLowerCase() !==
        OWNER_USERNAME.toLowerCase()
      ) {
        await sendMessage(chatId, "Hanya owner.");

        return res.status(200).send("ok");
      }

      const args = text.split(" ").slice(1);

      for (let u of args) {
        allowedUsers.add(
          u.replace("@", "").toLowerCase()
        );
      }

      await sendMessage(chatId, "User ditambah");

      return res.status(200).send("ok");
    }

    // =========================
    // REMOVE USER
    // =========================
    if (text.startsWith("/removeuser")) {
      if (
        username.toLowerCase() !==
        OWNER_USERNAME.toLowerCase()
      ) {
        await sendMessage(chatId, "Hanya owner.");

        return res.status(200).send("ok");
      }

      const args = text.split(" ").slice(1);

      for (let u of args) {
        allowedUsers.delete(
          u.replace("@", "").toLowerCase()
        );
      }

      await sendMessage(chatId, "User dihapus");

      return res.status(200).send("ok");
    }

    // =========================
    // AMBIL LIST
    // =========================
    const savedText = dataUser[chatId];

    if (
      text === "/rekap" ||
      text === "/rekap_win" ||
      text === "/refund"
    ) {
      if (!savedText) {
        await sendMessage(
          chatId,
          "Kirim list dulu."
        );

        return res.status(200).send("ok");
      }

      const parts = savedText
        .split(/\n\s*\n/)
        .filter((x) => x.trim());

      if (parts.length < 2) {
        await sendMessage(
          chatId,
          "Format list salah."
        );

        return res.status(200).send("ok");
      }

      const t1 = parts[0];
      const t2 = parts[1];

      const n1 = t1
        .split("\n")[0]
        .replace(":", "")
        .trim();

      const n2 = t2
        .split("\n")[0]
        .replace(":", "")
        .trim();

      const tim1 = parseList(t1);
      const tim2 = parseList(t2);

      // =========================
      // REKAP
      // =========================
      if (text === "/rekap") {
        const total1 = tim1.reduce(
          (a, b) => a + b.saldo,
          0
        );

        const total2 = tim2.reduce(
          (a, b) => a + b.saldo,
          0
        );

        const selisih = Math.abs(
          total1 - total2
        );

        let hasil = "SEIMBANG";

        if (total1 > total2) {
          hasil = `${n2} KEKURANGAN ${selisih}K`;
        } else if (total2 > total1) {
          hasil = `${n1} KEKURANGAN ${selisih}K`;
        }

        await sendMessage(
          chatId,
          `${n1}: ${total1}K\n${n2}: ${total2}K\n\nSELISIH: ${selisih}K\n${hasil}`
        );
      }

      // =========================
      // REKAP WIN
      // =========================
      if (text === "/rekap_win") {
        let hasil = "";
        let totalFee = 0;

        hasil += `${n1}:\n`;

        for (let p of tim1) {
          const fee = hitungFee(p.saldo);

          const terima = p.lf
            ? p.saldo - fee
            : p.saldo * 2 - fee;

          totalFee += fee;

          hasil += `${p.nama} ${p.saldo}//${terima}\n`;
        }

        hasil += `\n${n2}:\n`;

        for (let p of tim2) {
          const fee = hitungFee(p.saldo);

          const terima = p.lf
            ? p.saldo - fee
            : p.saldo * 2 - fee;

          totalFee += fee;

          hasil += `${p.nama} ${p.saldo}//${terima}\n`;
        }

        hasil += `\nTOTAL FEE = ${totalFee}K`;

        await sendMessage(chatId, hasil);
      }

      // =========================
      // REFUND
      // =========================
      if (text === "/refund") {
        let hasil = "";
        let totalFee = 0;

        hasil += `${n1}:\n`;

        for (let p of tim1) {
          const fee = hitungFee(p.saldo);

          const kembali =
            p.saldo - fee;

          totalFee += fee;

          hasil += `${p.nama} ${p.saldo}//${kembali}\n`;
        }

        hasil += `\n${n2}:\n`;

        for (let p of tim2) {
          const fee = hitungFee(p.saldo);

          const kembali =
            p.saldo - fee;

          totalFee += fee;

          hasil += `${p.nama} ${p.saldo}//${kembali}\n`;
        }

        hasil += `\nTOTAL FEE = ${totalFee}K`;

        await sendMessage(chatId, hasil);
      }
    }

    return res.status(200).send("ok");
  } catch (e) {
    console.log(e);

    return res.status(500).send("error");
  }
};