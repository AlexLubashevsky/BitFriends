import React, { useEffect, useState } from 'react';
import './App.css';

// Telegram WebApp integration
declare global {
  interface Window {
    Telegram?: any;
  }
}

interface Pet {
  hunger: number;
  happiness: number;
  skin: string;
  coins: number;
  owned_skins: string[];
}

const defaultPet: Pet = {
  hunger: 50,
  happiness: 50,
  skin: 'default',
  coins: 100,
  owned_skins: ['default'],
};

const SKINS: Record<string, { name: string; img: string; sol_price?: number; eth_price?: number }> = {
  default: {
    name: 'Default',
    img: 'https://i.imgur.com/8Km9tLL.png',
  },
  cat: {
    name: 'Cat',
    img: 'https://i.imgur.com/J5LVHEL.png',
    sol_price: 0.01,
    eth_price: 0.0005,
  },
  fox: {
    name: 'Fox',
    img: 'https://i.imgur.com/2yaf2wb.png',
    sol_price: 0.02,
    eth_price: 0.001,
  },
};

const SOL_RECEIVER = '4WF1wGepvyZ8sL9iTnLs7skvCqpDgiZPM9zTeUfk5nkQ';
const ETH_RECEIVER = '0x7C52A0C0b097134Dd2719bf26f63831a5bd20D44';
const API_URL = 'http://localhost:8000'; // Change to your backend URL if deployed

function App() {
  const [pet, setPet] = useState<Pet>(defaultPet);
  const [user, setUser] = useState<any>(null);
  const [showShop, setShowShop] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPayment, setShowPayment] = useState<null | { skin: string; chain: 'sol' | 'eth' }>();
  const [txInput, setTxInput] = useState('');
  const [paymentMsg, setPaymentMsg] = useState('');

  // Get Telegram user ID
  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      window.Telegram.WebApp.ready();
      setUser(window.Telegram.WebApp.initDataUnsafe?.user);
      document.body.className = window.Telegram.WebApp.colorScheme === 'dark' ? 'dark' : '';
    }
  }, []);

  // Fetch pet data from backend
  useEffect(() => {
    if (user) {
      setLoading(true);
      fetch(`${API_URL}/pet/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id }),
      })
        .then((res) => res.json())
        .then((data) => setPet(data))
        .finally(() => setLoading(false));
    }
  }, [user]);

  const apiAction = async (endpoint: string, body: any) => {
    setLoading(true);
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    setPet(data);
    setLoading(false);
  };

  const feedPet = () => user && apiAction('/pet/feed', { user_id: user.id });
  const playWithPet = () => user && apiAction('/pet/play', { user_id: user.id });
  const setSkin = (skin: string) => user && apiAction('/pet/set_skin', { user_id: user.id, skin });
  const buySkin = (skin: string) => user && apiAction('/shop/buy', { user_id: user.id, skin });

  // Payment flow
  const openPayment = (skin: string, chain: 'sol' | 'eth') => {
    setShowPayment({ skin, chain });
    setTxInput('');
    setPaymentMsg('');
  };
  const closePayment = () => {
    setShowPayment(null);
    setTxInput('');
    setPaymentMsg('');
  };
  const confirmPayment = async () => {
    if (!user || !showPayment) return;
    setLoading(true);
    setPaymentMsg('Verifying payment...');
    const res = await fetch(`${API_URL}/shop/confirm_payment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: user.id,
        skin: showPayment.skin,
        tx: txInput,
        chain: showPayment.chain,
      }),
    });
    const data = await res.json();
    setPet(data);
    setLoading(false);
    setPaymentMsg('Payment checked! If successful, your skin is now owned.');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h2>BitFriends 🐾</h2>
        {loading && <div className="loading">Loading...</div>}
        <div className="pet-card">
          <img src={SKINS[pet.skin].img} alt="pet" className="pet-img" />
          <div className="pet-status">
            <div>Hunger: {pet.hunger}</div>
            <div>Happiness: {pet.happiness}</div>
            <div>Skin: {SKINS[pet.skin].name}</div>
            <div>Coins: {pet.coins}</div>
          </div>
        </div>
        <div className="actions">
          <button onClick={feedPet} disabled={loading}>🍖 Feed</button>
          <button onClick={playWithPet} disabled={loading}>🎾 Play</button>
          <button onClick={() => setShowShop(true)}>🛍️ Shop</button>
        </div>
        <div className="owned-skins">
          <h4>Owned Skins</h4>
          <div className="skin-list">
            {pet.owned_skins.map((skin) => (
              <button
                key={skin}
                className={skin === pet.skin ? 'active' : ''}
                onClick={() => setSkin(skin)}
                disabled={skin === pet.skin || loading}
              >
                <img src={SKINS[skin].img} alt={SKINS[skin].name} className="skin-thumb" />
                {SKINS[skin].name}
              </button>
            ))}
          </div>
        </div>
        {showShop && (
          <div className="shop-modal">
            <h3>Pet Skin Shop</h3>
            <div className="shop-list">
              {Object.entries(SKINS).map(([key, skin]) => (
                <div key={key} className="shop-item">
                  <img src={skin.img} alt={skin.name} className="shop-img" />
                  <div>{skin.name}</div>
                  {pet.owned_skins.includes(key) ? (
                    <span className="owned">Owned</span>
                  ) : (
                    <>
                      <button onClick={() => buySkin(key)} disabled={loading}>Buy (coins)</button>
                      {skin.sol_price && (
                        <button onClick={() => openPayment(key, 'sol')} disabled={loading}>
                          Buy with SOL
                        </button>
                      )}
                      {skin.eth_price && (
                        <button onClick={() => openPayment(key, 'eth')} disabled={loading}>
                          Buy with ETH
                        </button>
                      )}
                    </>
                  )}
                </div>
              ))}
            </div>
            <button onClick={() => setShowShop(false)}>Close</button>
          </div>
        )}
        {showPayment && (
          <div className="payment-modal">
            <h3>Pay with {showPayment.chain === 'sol' ? 'Solana' : 'Ethereum'}</h3>
            <div>
              Send {showPayment.chain === 'sol' ? SKINS[showPayment.skin].sol_price + ' SOL' : SKINS[showPayment.skin].eth_price + ' ETH'} to:<br />
              <b>{showPayment.chain === 'sol' ? SOL_RECEIVER : ETH_RECEIVER}</b>
            </div>
            <div style={{ margin: '10px 0' }}>
              <input
                type="text"
                placeholder={showPayment.chain === 'sol' ? 'Transaction Signature' : 'Transaction Hash'}
                value={txInput}
                onChange={e => setTxInput(e.target.value)}
                style={{ width: '90%' }}
              />
            </div>
            <button onClick={confirmPayment} disabled={loading || !txInput}>
              Confirm Payment
            </button>
            <button onClick={closePayment} style={{ marginLeft: 8 }}>Cancel</button>
            {paymentMsg && <div style={{ marginTop: 8 }}>{paymentMsg}</div>}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
