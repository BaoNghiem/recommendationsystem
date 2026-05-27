import React, { useState, useEffect } from 'react';
import axios from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import {
  BarChart3, Users, Film, Star, TrendingUp, RefreshCw, Database,
  ArrowLeft
} from 'lucide-react';

export default function AdminDashboard({ onBack }) {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchStats = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get('/admin/stats');
      setStats(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
    setLoading(false);
  };

  useEffect(() => { fetchStats(); }, []);

  // Rating distribution chart
  const renderBarChart = (distribution) => {
    if (!distribution) return null;
    const entries = Object.entries(distribution).sort((a, b) => parseFloat(a[0]) - parseFloat(b[0]));
    const maxVal = Math.max(...entries.map(e => e[1]));

    return (
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', height: '200px', padding: '0 8px' }}>
        {entries.map(([star, count]) => {
          const pct = maxVal > 0 ? (count / maxVal) * 100 : 0;
          const hue = parseFloat(star) >= 4 ? 140 : parseFloat(star) >= 3 ? 50 : 0;
          return (
            <div key={star} style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              flex: 1, minWidth: 0
            }}>
              <span style={{
                fontSize: '11px', color: '#a1a1aa', marginBottom: '4px', fontWeight: 600
              }}>
                {count >= 1000 ? `${(count / 1000).toFixed(0)}K` : count}
              </span>
              <div style={{
                width: '100%', maxWidth: '40px',
                height: `${Math.max(pct, 4)}%`,
                background: `linear-gradient(180deg, hsl(${hue}, 80%, 55%), hsl(${hue}, 70%, 35%))`,
                borderRadius: '6px 6px 2px 2px',
                transition: 'height 0.8s cubic-bezier(.4,0,.2,1)',
                boxShadow: `0 0 12px hsl(${hue}, 80%, 40%, 0.3)`
              }} />
              <span style={{
                fontSize: '11px', color: '#d4d4d8', marginTop: '6px', fontWeight: 700
              }}>
                {star}★
              </span>
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        minHeight: '60vh', color: '#a1a1aa'
      }}>
        <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite' }} />
        <span style={{ marginLeft: 12, fontSize: 18 }}>Đang tải dữ liệu thống kê...</span>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
        alignItems: 'center', minHeight: '60vh', color: '#ef4444'
      }}>
        <p style={{ fontSize: 18 }}>❌ Lỗi: {error}</p>
        <button onClick={fetchStats} style={{
          marginTop: 16, padding: '10px 24px', background: '#dc2626',
          border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontWeight: 600
        }}>
          Thử lại
        </button>
      </div>
    );
  }

  const statCards = [
    {
      icon: <Users size={28} />, label: 'Tổng người dùng',
      value: stats.total_users?.toLocaleString(),
      sub: `${stats.real_users?.toLocaleString()} tài khoản thực`,
      gradient: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
      glow: 'rgba(99,102,241,0.3)'
    },
    {
      icon: <Film size={28} />, label: 'Tổng số phim',
      value: stats.total_movies?.toLocaleString(),
      sub: 'trong cơ sở dữ liệu',
      gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)',
      glow: 'rgba(6,182,212,0.3)'
    },
    {
      icon: <Star size={28} />, label: 'Tổng lượt đánh giá',
      value: stats.total_ratings?.toLocaleString(),
      sub: 'ratings trong hệ thống',
      gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
      glow: 'rgba(245,158,11,0.3)'
    },
    {
      icon: <Database size={28} />, label: 'Tỉ lệ dữ liệu',
      value: stats.total_users > 0
        ? `${((stats.total_ratings / (stats.total_users * stats.total_movies)) * 100).toFixed(2)}%`
        : '0%',
      sub: 'Ma trận tương tác (Sparsity)',
      gradient: 'linear-gradient(135deg, #10b981, #059669)',
      glow: 'rgba(16,185,129,0.3)'
    },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 16px' }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 32
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {onBack && (
            <button onClick={onBack} style={{
              background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 10, padding: '8px 12px', color: '#d4d4d8', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6, fontSize: 14
            }}>
              <ArrowLeft size={18} /> Trang chủ
            </button>
          )}
          <div>
            <h1 style={{
              fontSize: 28, fontWeight: 800, color: '#fff', margin: 0,
              display: 'flex', alignItems: 'center', gap: 10
            }}>
              <BarChart3 size={30} style={{ color: '#818cf8' }} />
              Admin Dashboard
            </h1>
            <p style={{ color: '#71717a', margin: '4px 0 0', fontSize: 14 }}>
              Tổng quan hệ thống Movie Recommender AI
            </p>
          </div>
        </div>
        <button onClick={fetchStats} style={{
          background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 10, padding: '10px 20px', color: '#a1a1aa', cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600,
          transition: 'all 0.2s'
        }}
          onMouseEnter={e => { e.target.style.background = 'rgba(255,255,255,0.12)'; e.target.style.color = '#fff'; }}
          onMouseLeave={e => { e.target.style.background = 'rgba(255,255,255,0.06)'; e.target.style.color = '#a1a1aa'; }}
        >
          <RefreshCw size={16} /> Làm mới
        </button>
      </div>

      {/* Stat Cards */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 20, marginBottom: 32
      }}>
        {statCards.map((card, i) => (
          <div key={i} style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 16, padding: '24px 20px',
            transition: 'all 0.3s',
            cursor: 'default',
            position: 'relative', overflow: 'hidden'
          }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = `0 12px 40px ${card.glow}`;
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)';
            }}
          >
            <div style={{
              position: 'absolute', top: -20, right: -20, width: 80, height: 80,
              background: card.gradient, borderRadius: '50%', opacity: 0.12, filter: 'blur(20px)'
            }} />
            <div style={{
              display: 'inline-flex', padding: 10, borderRadius: 12,
              background: card.gradient, marginBottom: 14
            }}>
              {React.cloneElement(card.icon, { color: '#fff' })}
            </div>
            <p style={{ color: '#a1a1aa', fontSize: 13, margin: '0 0 4px', fontWeight: 500 }}>
              {card.label}
            </p>
            <p style={{
              color: '#fff', fontSize: 32, fontWeight: 800, margin: '0 0 4px',
              letterSpacing: '-0.02em'
            }}>
              {card.value}
            </p>
            <p style={{ color: '#71717a', fontSize: 12, margin: 0 }}>{card.sub}</p>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
        gap: 20
      }}>
        {/* Rating Distribution Chart */}
        <div style={{
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 16, padding: '24px'
        }}>
          <h3 style={{
            fontSize: 16, fontWeight: 700, color: '#fff', margin: '0 0 20px',
            display: 'flex', alignItems: 'center', gap: 8
          }}>
            <Star size={20} style={{ color: '#f59e0b' }} />
            Phân bố Rating theo Sao
          </h3>
          {renderBarChart(stats.rating_distribution)}
        </div>

        {/* Top Rated Movies */}
        <div style={{
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 16, padding: '24px'
        }}>
          <h3 style={{
            fontSize: 16, fontWeight: 700, color: '#fff', margin: '0 0 20px',
            display: 'flex', alignItems: 'center', gap: 8
          }}>
            <TrendingUp size={20} style={{ color: '#10b981' }} />
            Top 5 Phim Nhiều Lượt Đánh Giá Nhất
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {stats.top_rated_movies?.map((movie, i) => {
              const maxCount = stats.top_rated_movies[0]?.count || 1;
              const pct = (movie.count / maxCount) * 100;
              return (
                <div key={i}>
                  <div style={{
                    display: 'flex', justifyContent: 'space-between', marginBottom: 4
                  }}>
                    <span style={{
                      color: '#d4d4d8', fontSize: 13, fontWeight: 600,
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      maxWidth: '70%'
                    }}>
                      {i + 1}. {movie.title}
                    </span>
                    <span style={{ color: '#a1a1aa', fontSize: 12, fontWeight: 700 }}>
                      {movie.count?.toLocaleString()} ratings
                    </span>
                  </div>
                  <div style={{
                    width: '100%', height: 6, background: 'rgba(255,255,255,0.06)',
                    borderRadius: 3, overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${pct}%`, height: '100%',
                      background: 'linear-gradient(90deg, #10b981, #34d399)',
                      borderRadius: 3,
                      transition: 'width 1s cubic-bezier(.4,0,.2,1)'
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
