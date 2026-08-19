import React from 'react';
// HashRouter: rotas ficam após o '#' (ex.: /donaspainel/#/cadastro).
// Vantagem: refresh funciona em qualquer servidor estático (VPS, Netlify, etc.)
// sem precisar configurar fallback no nginx.
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import AdminLogin from './admin/AdminLogin';
import AdminLayout from './admin/AdminLayout';
import AdminDashboard from './admin/AdminDashboard';
import AdminInscriptions from './admin/AdminInscriptions';
import AdminUsers from './admin/AdminUsers';
import AdminCadastros from './admin/AdminCadastros';
import AdminProfile from './admin/AdminProfile';
import AdminSettings from './admin/AdminSettings';

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/login" element={<AdminLogin/>}/>
        <Route path="/" element={<AdminLayout/>}>
          <Route index element={<AdminDashboard/>}/>
          <Route path="dashboard" element={<AdminDashboard/>}/>
          <Route path="inscricoes" element={<AdminInscriptions/>}/>
          <Route path="cadastro" element={<AdminCadastros/>}/>
          <Route path="perfil" element={<AdminProfile/>}/>
          <Route path="usuarios" element={<AdminUsers/>}/>
          <Route path="configuracoes" element={<AdminSettings/>}/>
        </Route>
        <Route path="*" element={<Navigate to="/login" replace/>}/>
      </Routes>
    </HashRouter>
  );
}
