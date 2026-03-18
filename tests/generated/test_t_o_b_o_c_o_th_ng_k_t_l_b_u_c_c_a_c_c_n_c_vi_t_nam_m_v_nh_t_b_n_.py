from __future__ import annotations
import pytest
from app.skills.dynamic.t_o_b_o_c_o_th_ng_k_t_l_b_u_c_c_a_c_c_n_c_vi_t_nam_m_v_nh_t_b_n_ import run

def test_run():
    result = run()
    assert isinstance(result, dict)
    assert 'status' in result
