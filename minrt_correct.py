#!/usr/bin/env python3
"""
Correct Min-RT Implementation
Direct port from min-rt.ml with all features
"""

import math
import sys


class MinRT:
    def __init__(self):
        # Initialize all global arrays matching globals.ml
        self.objects = []
        self.size = [128, 128]
        self.dbg = [True]
        self.screen = [0.0, 0.0, 0.0]
        self.vp = [0.0, 0.0, 0.0]
        self.view = [0.0, 0.0, 0.0]
        self.light = [0.0, 0.0, 0.0]
        self.cos_v = [0.0, 0.0]
        self.sin_v = [0.0, 0.0]
        self.beam = [255.0]
        self.and_net = []
        self.or_net = [[]]

        # Working variables
        self.temp = [0.0] * 14
        self.cs_temp = [0.0] * 16
        self.solver_dist = [0.0]
        self.vscan = [0.0, 0.0, 0.0]
        self.intsec_rectside = [0]
        self.tmin = [1000000000.0]
        self.crashed_point = [0.0, 0.0, 0.0]
        self.crashed_object = [0]
        self.end_flag = [False]
        self.viewpoint = [0.0, 0.0, 0.0]
        self.nvector = [0.0, 0.0, 0.0]
        self.rgb = [0.0, 0.0, 0.0]
        self.texture_color = [0.0, 0.0, 0.0]
        self.solver_w_vec = [0.0, 0.0, 0.0]
        self.chkinside_p = [0.0, 0.0, 0.0]
        self.isoutside_q = [0.0, 0.0, 0.0]
        self.nvector_w = [0.0, 0.0, 0.0]

        # Main loop variables
        self.scan_d = [0.0]
        self.scan_offset = [0.0]
        self.scan_sscany = [0.0]
        self.scan_met1 = [0.0]
        self.wscan = [0.0, 0.0, 0.0]

    # Utility functions
    def xor(self, x, y):
        return (x and not y) or (not x and y)

    def fsqr(self, x):
        return x * x

    def fhalf(self, x):
        return x / 2.0

    def sgn(self, x):
        return 1.0 if x > 0.0 else -1.0

    def rad(self, x):
        return x * 0.017453293

    # Object accessors
    def o_texturetype(self, m):
        return m['texture']

    def o_form(self, m):
        return m['form']

    def o_reflectiontype(self, m):
        return m['refltype']

    def o_isinvert(self, m):
        return m['invert']

    def o_isrot(self, m):
        return m['isrot']

    def o_param_a(self, m):
        return m['abc'][0]

    def o_param_b(self, m):
        return m['abc'][1]

    def o_param_c(self, m):
        return m['abc'][2]

    def o_param_x(self, m):
        return m['xyz'][0]

    def o_param_y(self, m):
        return m['xyz'][1]

    def o_param_z(self, m):
        return m['xyz'][2]

    def o_diffuse(self, m):
        return m['reflparam'][0]

    def o_hilight(self, m):
        return m['reflparam'][1]

    def o_color_red(self, m):
        return m['color'][0]

    def o_color_green(self, m):
        return m['color'][1]

    def o_color_blue(self, m):
        return m['color'][2]

    def o_param_r1(self, m):
        return m['rotation'][0]

    def o_param_r2(self, m):
        return m['rotation'][1]

    def o_param_r3(self, m):
        return m['rotation'][2]

    def normalize_vector(self, v, inv):
        n0 = math.sqrt(self.fsqr(v[0]) + self.fsqr(v[1]) + self.fsqr(v[2]))
        if n0 < 1e-10:
            return
        n = -n0 if inv else n0
        v[0] /= n
        v[1] /= n
        v[2] /= n

    # Read functions
    def read_environ(self, input_data, idx):
        self.screen[0] = input_data[idx[0]]; idx[0] += 1
        self.screen[1] = input_data[idx[0]]; idx[0] += 1
        self.screen[2] = input_data[idx[0]]; idx[0] += 1

        v1 = self.rad(input_data[idx[0]]); idx[0] += 1
        self.cos_v[0] = math.cos(v1)
        self.sin_v[0] = math.sin(v1)

        v2 = self.rad(input_data[idx[0]]); idx[0] += 1
        self.cos_v[1] = math.cos(v2)
        self.sin_v[1] = math.sin(v2)

        nl = input_data[idx[0]]; idx[0] += 1

        l1 = self.rad(input_data[idx[0]]); idx[0] += 1
        sl1 = math.sin(l1)
        self.light[1] = -sl1

        l2 = self.rad(input_data[idx[0]]); idx[0] += 1
        cl1 = math.cos(l1)
        sl2 = math.sin(l2)
        self.light[0] = cl1 * sl2

        cl2 = math.cos(l2)
        self.light[2] = cl1 * cl2

        self.beam[0] = input_data[idx[0]]; idx[0] += 1

        self.vp[0] = self.cos_v[0] * self.sin_v[1] * (-200.0)
        self.vp[1] = (-self.sin_v[0]) * (-200.0)
        self.vp[2] = self.cos_v[0] * self.cos_v[1] * (-200.0)

        self.view[0] = self.vp[0] + self.screen[0]
        self.view[1] = self.vp[1] + self.screen[1]
        self.view[2] = self.vp[2] + self.screen[2]

    def read_nth_object(self, n, input_data, idx):
        texture = int(input_data[idx[0]]); idx[0] += 1
        if texture == -1:
            return False

        form = int(input_data[idx[0]]); idx[0] += 1
        refltype = int(input_data[idx[0]]); idx[0] += 1
        isrot_p = int(input_data[idx[0]]); idx[0] += 1

        abc = [input_data[idx[0]], input_data[idx[0]+1], input_data[idx[0]+2]]
        idx[0] += 3

        xyz = [input_data[idx[0]], input_data[idx[0]+1], input_data[idx[0]+2]]
        idx[0] += 3

        m_invert = input_data[idx[0]] < 0.0
        idx[0] += 1

        reflparam = [input_data[idx[0]], input_data[idx[0]+1]]
        idx[0] += 2

        color = [input_data[idx[0]], input_data[idx[0]+1], input_data[idx[0]+2]]
        idx[0] += 3

        rotation = [0.0, 0.0, 0.0]
        if isrot_p != 0:
            rotation = [self.rad(input_data[idx[0]]), self.rad(input_data[idx[0]+1]), self.rad(input_data[idx[0]+2])]
            idx[0] += 3

        m_invert2 = True if form == 2 else m_invert

        obj = {
            'texture': texture,
            'form': form,
            'refltype': refltype,
            'isrot': isrot_p,
            'abc': abc,
            'xyz': xyz,
            'invert': m_invert2,
            'reflparam': reflparam,
            'color': color,
            'rotation': rotation
        }

        # Normalization
        if form == 3:
            for i in range(3):
                a = abc[i]
                abc[i] = (self.sgn(a) / self.fsqr(a)) if a != 0.0 else 0.0
        elif form == 2:
            self.normalize_vector(abc, not m_invert)

        # Rotation handling
        if isrot_p != 0:
            cs = self.cs_temp
            cs[10] = math.cos(rotation[0])
            cs[11] = math.sin(rotation[0])
            cs[12] = math.cos(rotation[1])
            cs[13] = math.sin(rotation[1])
            cs[14] = math.cos(rotation[2])
            cs[15] = math.sin(rotation[2])

            cs[0] = cs[12] * cs[14]
            cs[1] = cs[11] * cs[13] * cs[14] - cs[10] * cs[15]
            cs[2] = cs[10] * cs[13] * cs[14] + cs[11] * cs[15]
            cs[3] = cs[12] * cs[15]
            cs[4] = cs[11] * cs[13] * cs[15] + cs[10] * cs[14]
            cs[5] = cs[10] * cs[13] * cs[15] - cs[11] * cs[14]
            cs[6] = -cs[13]
            cs[7] = cs[11] * cs[12]
            cs[8] = cs[10] * cs[12]

            ao, bo, co = abc[0], abc[1], abc[2]
            abc[0] = ao * self.fsqr(cs[0]) + bo * self.fsqr(cs[3]) + co * self.fsqr(cs[6])
            abc[1] = ao * self.fsqr(cs[1]) + bo * self.fsqr(cs[4]) + co * self.fsqr(cs[7])
            abc[2] = ao * self.fsqr(cs[2]) + bo * self.fsqr(cs[5]) + co * self.fsqr(cs[8])

            rotation[0] = 2.0 * (ao * cs[1] * cs[2] + bo * cs[4] * cs[5] + co * cs[7] * cs[8])
            rotation[1] = 2.0 * (ao * cs[0] * cs[2] + bo * cs[3] * cs[5] + co * cs[6] * cs[8])
            rotation[2] = 2.0 * (ao * cs[0] * cs[1] + bo * cs[3] * cs[4] + co * cs[6] * cs[7])

        self.objects.append(obj)
        return True

    def read_all_object(self, input_data, idx):
        n = 0
        while n < 61:
            if not self.read_nth_object(n, input_data, idx):
                break
            n += 1

    def read_net_item(self, input_data, idx):
        items = []
        while True:
            val = int(input_data[idx[0]])
            idx[0] += 1
            if val == -1:
                break
            items.append(val)
        return items

    def read_and_network(self, input_data, idx):
        nets = []
        while True:
            net = self.read_net_item(input_data, idx)
            if len(net) == 0:
                break
            nets.append(net)
        return nets

    def read_or_network(self, input_data, idx):
        nets = []
        while True:
            first = int(input_data[idx[0]])
            idx[0] += 1
            if first == -1:
                nets.append([-1])  # Add terminator entry
                break
            net = [first] + self.read_net_item(input_data, idx)
            nets.append(net)
        return nets

    def read_parameter(self, input_data):
        idx = [0]
        self.read_environ(input_data, idx)
        self.read_all_object(input_data, idx)
        self.and_net = self.read_and_network(input_data, idx)
        self.or_net = [self.read_or_network(input_data, idx)]

    # Solver functions
    def solver_rect(self, m, l):
        o_param_a = self.o_param_a(m)
        o_param_b = self.o_param_b(m)
        o_param_c = self.o_param_c(m)
        o_isinvert = self.o_isinvert(m)

        # YZ plane
        if l[0] != 0.0:
            d = o_param_a if self.xor(o_isinvert, l[0] < 0.0) else -o_param_a
            d2 = (d - self.solver_w_vec[0]) / l[0]
            if abs(d2 * l[1] + self.solver_w_vec[1]) < o_param_b:
                if abs(d2 * l[2] + self.solver_w_vec[2]) < o_param_c:
                    self.solver_dist[0] = d2
                    return 1

        # ZX plane
        if l[1] != 0.0:
            d = o_param_b if self.xor(o_isinvert, l[1] < 0.0) else -o_param_b
            d2 = (d - self.solver_w_vec[1]) / l[1]
            if abs(d2 * l[2] + self.solver_w_vec[2]) < o_param_c:
                if abs(d2 * l[0] + self.solver_w_vec[0]) < o_param_a:
                    self.solver_dist[0] = d2
                    return 2

        # XY plane
        if l[2] != 0.0:
            d = o_param_c if self.xor(o_isinvert, l[2] < 0.0) else -o_param_c
            d2 = (d - self.solver_w_vec[2]) / l[2]
            if abs(d2 * l[0] + self.solver_w_vec[0]) < o_param_a:
                if abs(d2 * l[1] + self.solver_w_vec[1]) < o_param_b:
                    self.solver_dist[0] = d2
                    return 3

        return 0

    def solver_surface(self, m, l):
        q = l[0] * self.o_param_a(m) + l[1] * self.o_param_b(m) + l[2] * self.o_param_c(m)
        if q > 0.0:
            t = (self.solver_w_vec[0] * self.o_param_a(m) +
                 self.solver_w_vec[1] * self.o_param_b(m) +
                 self.solver_w_vec[2] * self.o_param_c(m)) / q
            self.solver_dist[0] = -t
            return 1
        return 0

    def in_prod_sqr_obj(self, m, v):
        return (self.fsqr(v[0]) * self.o_param_a(m) +
                self.fsqr(v[1]) * self.o_param_b(m) +
                self.fsqr(v[2]) * self.o_param_c(m))

    def in_prod_co_objrot(self, m, v):
        return (v[1] * v[2] * self.o_param_r1(m) +
                v[0] * v[2] * self.o_param_r2(m) +
                v[0] * v[1] * self.o_param_r3(m))

    def solver2nd_mul_b(self, m, l):
        return (self.solver_w_vec[0] * l[0] * self.o_param_a(m) +
                self.solver_w_vec[1] * l[1] * self.o_param_b(m) +
                self.solver_w_vec[2] * l[2] * self.o_param_c(m))

    def solver2nd_rot_b(self, m, l):
        return ((self.solver_w_vec[2] * l[1] + self.solver_w_vec[1] * l[2]) * self.o_param_r1(m) +
                (self.solver_w_vec[0] * l[2] + self.solver_w_vec[2] * l[0]) * self.o_param_r2(m) +
                (self.solver_w_vec[0] * l[1] + self.solver_w_vec[1] * l[0]) * self.o_param_r3(m))

    def solver_second(self, m, l):
        aa0 = self.in_prod_sqr_obj(m, l)
        aa = aa0 + self.in_prod_co_objrot(m, l) if self.o_isrot(m) != 0 else aa0

        if aa == 0.0:
            return 0

        bb0 = 2.0 * self.solver2nd_mul_b(m, l)
        bb = bb0 + self.solver2nd_rot_b(m, l) if self.o_isrot(m) != 0 else bb0

        cc0 = self.in_prod_sqr_obj(m, self.solver_w_vec)
        cc1 = cc0 + self.in_prod_co_objrot(m, self.solver_w_vec) if self.o_isrot(m) != 0 else cc0
        cc = cc1 - 1.0 if self.o_form(m) == 3 else cc1

        d = self.fsqr(bb) - 4.0 * aa * cc

        if d > 0.0:
            sd = math.sqrt(d)
            t1 = sd if self.o_isinvert(m) else -sd
            self.solver_dist[0] = (t1 - bb) / (2.0 * aa)
            return 1
        return 0

    def solver(self, index, l, p):
        m = self.objects[index]
        self.solver_w_vec[0] = p[0] - self.o_param_x(m)
        self.solver_w_vec[1] = p[1] - self.o_param_y(m)
        self.solver_w_vec[2] = p[2] - self.o_param_z(m)

        m_shape = self.o_form(m)
        if m_shape == 1:
            return self.solver_rect(m, l)
        elif m_shape == 2:
            return self.solver_surface(m, l)
        else:
            return self.solver_second(m, l)

    # Inside/Outside checks
    def is_rect_outside(self, m):
        q = self.isoutside_q
        if (abs(q[0]) < self.o_param_a(m) and
            abs(q[1]) < self.o_param_b(m) and
            abs(q[2]) < self.o_param_c(m)):
            return self.o_isinvert(m)
        return not self.o_isinvert(m)

    def is_plane_outside(self, m):
        w = (self.o_param_a(m) * self.isoutside_q[0] +
             self.o_param_b(m) * self.isoutside_q[1] +
             self.o_param_c(m) * self.isoutside_q[2])
        s = w < 0.0
        return not self.xor(self.o_isinvert(m), s)

    def is_second_outside(self, m):
        w = self.in_prod_sqr_obj(m, self.isoutside_q)
        w2 = w - 1.0 if self.o_form(m) == 3 else w
        w3 = w2 + self.in_prod_co_objrot(m, self.isoutside_q) if self.o_isrot(m) != 0 else w2
        s = w3 < 0.0
        return not self.xor(self.o_isinvert(m), s)

    def is_outside(self, m):
        self.isoutside_q[0] = self.chkinside_p[0] - self.o_param_x(m)
        self.isoutside_q[1] = self.chkinside_p[1] - self.o_param_y(m)
        self.isoutside_q[2] = self.chkinside_p[2] - self.o_param_z(m)

        m_shape = self.o_form(m)
        if m_shape == 1:
            return self.is_rect_outside(m)
        elif m_shape == 2:
            return self.is_plane_outside(m)
        else:
            return self.is_second_outside(m)

    def check_all_inside(self, ofs, iand):
        if ofs >= len(iand) or iand[ofs] == -1:
            return True
        if self.is_outside(self.objects[iand[ofs]]):
            return False
        return self.check_all_inside(ofs + 1, iand)

    # Shadow check
    def shadow_check_and_group(self, iand_ofs, and_group, p):
        if iand_ofs >= len(and_group) or and_group[iand_ofs] == -1:
            return False

        obj = and_group[iand_ofs]
        t0 = self.solver(obj, self.light, p)
        t0p = self.solver_dist[0]

        if t0 != 0 and t0p < -0.2:
            t = t0p + 0.01
            self.chkinside_p[0] = self.light[0] * t + p[0]
            self.chkinside_p[1] = self.light[1] * t + p[1]
            self.chkinside_p[2] = self.light[2] * t + p[2]

            if self.check_all_inside(0, and_group):
                return True
            return self.shadow_check_and_group(iand_ofs + 1, and_group, p)
        else:
            if self.o_isinvert(self.objects[obj]):
                return self.shadow_check_and_group(iand_ofs + 1, and_group, p)
            return False

    def shadow_check_one_or_group(self, ofs, or_group, p):
        if ofs >= len(or_group) or or_group[ofs] == -1:
            return False

        head = or_group[ofs]
        and_group = self.and_net[head]

        if self.shadow_check_and_group(0, and_group, p):
            return True
        return self.shadow_check_one_or_group(ofs + 1, or_group, p)

    def shadow_check_one_or_matrix(self, ofs, or_matrix, p):
        if ofs >= len(or_matrix):
            return False

        head = or_matrix[ofs]
        if len(head) == 0 or head[0] == -1:
            return False

        range_primitive = head[0]

        if range_primitive == 99:
            if self.shadow_check_one_or_group(1, head, p):
                return True
            return self.shadow_check_one_or_matrix(ofs + 1, or_matrix, p)
        else:
            t = self.solver(range_primitive, self.light, p)
            if t != 0 and self.solver_dist[0] < -0.1:
                if self.shadow_check_one_or_group(1, head, p):
                    return True
            return self.shadow_check_one_or_matrix(ofs + 1, or_matrix, p)

    # Get normal vector
    def get_nvector_rect(self):
        rectside = self.intsec_rectside[0]
        if rectside == 1:
            self.nvector[0] = -self.sgn(self.vscan[0])
            self.nvector[1] = 0.0
            self.nvector[2] = 0.0
        elif rectside == 2:
            self.nvector[0] = 0.0
            self.nvector[1] = -self.sgn(self.vscan[1])
            self.nvector[2] = 0.0
        elif rectside == 3:
            self.nvector[0] = 0.0
            self.nvector[1] = 0.0
            self.nvector[2] = -self.sgn(self.vscan[2])

    def get_nvector_plane(self, m):
        self.nvector[0] = -self.o_param_a(m)
        self.nvector[1] = -self.o_param_b(m)
        self.nvector[2] = -self.o_param_c(m)

    def get_nvector_second_norot(self, m, p):
        self.nvector[0] = (p[0] - self.o_param_x(m)) * self.o_param_a(m)
        self.nvector[1] = (p[1] - self.o_param_y(m)) * self.o_param_b(m)
        self.nvector[2] = (p[2] - self.o_param_z(m)) * self.o_param_c(m)
        self.normalize_vector(self.nvector, self.o_isinvert(m))

    def get_nvector_second_rot(self, m, p):
        self.nvector_w[0] = p[0] - self.o_param_x(m)
        self.nvector_w[1] = p[1] - self.o_param_y(m)
        self.nvector_w[2] = p[2] - self.o_param_z(m)

        self.nvector[0] = (self.nvector_w[0] * self.o_param_a(m) +
                          self.fhalf(self.nvector_w[1] * self.o_param_r3(m) +
                                    self.nvector_w[2] * self.o_param_r2(m)))
        self.nvector[1] = (self.nvector_w[1] * self.o_param_b(m) +
                          self.fhalf(self.nvector_w[0] * self.o_param_r3(m) +
                                    self.nvector_w[2] * self.o_param_r1(m)))
        self.nvector[2] = (self.nvector_w[2] * self.o_param_c(m) +
                          self.fhalf(self.nvector_w[0] * self.o_param_r2(m) +
                                    self.nvector_w[1] * self.o_param_r1(m)))
        self.normalize_vector(self.nvector, self.o_isinvert(m))

    def get_nvector(self, m, p):
        m_shape = self.o_form(m)
        if m_shape == 1:
            self.get_nvector_rect()
        elif m_shape == 2:
            self.get_nvector_plane(m)
        else:
            if self.o_isrot(m) != 0:
                self.get_nvector_second_rot(m, p)
            else:
                self.get_nvector_second_norot(m, p)

    # Texture
    def utexture(self, m, p):
        m_tex = self.o_texturetype(m)
        self.texture_color[0] = self.o_color_red(m)
        self.texture_color[1] = self.o_color_green(m)
        self.texture_color[2] = self.o_color_blue(m)

        if m_tex == 1:
            w1 = p[0] - self.o_param_x(m)
            d1 = math.floor(w1 * 0.05) * 20.0
            flag1 = (w1 - d1) < 10.0

            w3 = p[2] - self.o_param_z(m)
            d2 = math.floor(w3 * 0.05) * 20.0
            flag2 = (w3 - d2) < 10.0

            self.texture_color[1] = 255.0 if (flag1 == flag2) else 0.0

        elif m_tex == 2:
            w2 = self.fsqr(math.sin(p[1] * 0.25))
            self.texture_color[0] = 255.0 * w2
            self.texture_color[1] = 255.0 * (1.0 - w2)

        elif m_tex == 3:
            w1 = p[0] - self.o_param_x(m)
            w3 = p[2] - self.o_param_z(m)
            w2 = math.sqrt(self.fsqr(w1) + self.fsqr(w3)) / 10.0
            w4 = (w2 - math.floor(w2)) * 3.1415927
            cws = self.fsqr(math.cos(w4))
            self.texture_color[1] = cws * 255.0
            self.texture_color[2] = (1.0 - cws) * 255.0

        elif m_tex == 4:
            w1 = (p[0] - self.o_param_x(m)) * math.sqrt(abs(self.o_param_a(m)))
            w3 = (p[2] - self.o_param_z(m)) * math.sqrt(abs(self.o_param_c(m)))
            w4 = math.sqrt(self.fsqr(w1) + self.fsqr(w3))

            if abs(w1) < 1.0e-4:
                w7 = 15.0
            else:
                w5 = abs(w3 / w1)
                w7 = math.atan(w5) * (30.0 / 3.1415927)

            w9 = w7 - math.floor(w7)

            w2 = (p[1] - self.o_param_y(m)) * math.sqrt(abs(self.o_param_b(m)))

            if abs(w4) < 1.0e-4:
                w8 = 15.0
            else:
                w6 = abs(w2 / w4)
                w8 = math.atan(w6) * (30.0 / 3.1415927)

            w10 = w8 - math.floor(w8)
            w11 = 0.15 - self.fsqr(0.5 - w9) - self.fsqr(0.5 - w10)
            self.texture_color[2] = 0.0 if w11 <= 0.0 else w11 * (255.0 / 0.3)

    def in_prod(self, v1, v2):
        return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

    def accumulate_vec_mul(self, v1, v2, w):
        v1[0] += w * v2[0]
        v1[1] += w * v2[1]
        v1[2] += w * v2[2]

    # Main raytracing
    def raytracing(self, nref, energy):
        crashed_p = self.tracer(self.viewpoint, self.vscan)

        if not crashed_p:
            if nref != 0:
                hl = -self.in_prod(self.vscan, self.light)
                if hl > 0.0:
                    ihl = self.fsqr(hl) * hl * energy * self.beam[0]
                    self.rgb[0] += ihl
                    self.rgb[1] += ihl
                    self.rgb[2] += ihl
            return

        cobj = self.objects[self.crashed_object[0]]
        self.get_nvector(cobj, self.crashed_point)

        if self.shadow_check_one_or_matrix(0, self.or_net[0], self.crashed_point):
            bright = 0.0
        else:
            br = -self.in_prod(self.nvector, self.light)
            br1 = (br + 0.2) if br > 0.0 else 0.2
            bright = br1 * energy * self.o_diffuse(cobj)

        self.utexture(cobj, self.crashed_point)
        self.accumulate_vec_mul(self.rgb, self.texture_color, bright)

        if nref > 4 or energy <= 0.1:
            return

        w = -2.0 * self.in_prod(self.vscan, self.nvector)
        self.accumulate_vec_mul(self.vscan, self.nvector, w)

        m_surface = self.o_reflectiontype(cobj)

        if m_surface == 1:
            if self.o_hilight(cobj) != 0.0:
                hl = -self.in_prod(self.vscan, self.light)
                if hl > 0.0:
                    ihl = self.fsqr(self.fsqr(hl)) * energy * bright * self.o_hilight(cobj)
                    self.rgb[0] += ihl
                    self.rgb[1] += ihl
                    self.rgb[2] += ihl
        elif m_surface == 2:
            self.viewpoint[0] = self.crashed_point[0]
            self.viewpoint[1] = self.crashed_point[1]
            self.viewpoint[2] = self.crashed_point[2]
            energy2 = energy * (1.0 - self.o_diffuse(cobj))
            self.raytracing(nref + 1, energy2)

    # Tracer
    def solve_each_element(self, iand_ofs, and_group):
        if iand_ofs >= len(and_group) or and_group[iand_ofs] == -1:
            return

        iobj = and_group[iand_ofs]
        t0 = self.solver(iobj, self.vscan, self.viewpoint)

        if t0 != 0:
            t0p = self.solver_dist[0]
            if t0p > -0.1 and t0p < self.tmin[0]:
                t = t0p + 0.01
                self.chkinside_p[0] = self.vscan[0] * t + self.viewpoint[0]
                self.chkinside_p[1] = self.vscan[1] * t + self.viewpoint[1]
                self.chkinside_p[2] = self.vscan[2] * t + self.viewpoint[2]

                if self.check_all_inside(0, and_group):
                    self.tmin[0] = t
                    self.crashed_point[0] = self.chkinside_p[0]
                    self.crashed_point[1] = self.chkinside_p[1]
                    self.crashed_point[2] = self.chkinside_p[2]
                    self.intsec_rectside[0] = t0
                    self.crashed_object[0] = iobj
        else:
            if not self.o_isinvert(self.objects[iobj]):
                self.end_flag[0] = True

        if not self.end_flag[0]:
            self.solve_each_element(iand_ofs + 1, and_group)

    def solve_one_or_network(self, ofs, or_group):
        if ofs >= len(or_group) or or_group[ofs] == -1:
            return

        head = or_group[ofs]
        and_group = self.and_net[head]
        self.end_flag[0] = False
        self.solve_each_element(0, and_group)
        self.solve_one_or_network(ofs + 1, or_group)

    def trace_or_matrix(self, ofs, or_network):
        head = or_network[ofs]
        range_primitive = head[0]

        if range_primitive == -1:
            return

        if range_primitive == 99:
            self.solve_one_or_network(1, head)
        else:
            t = self.solver(range_primitive, self.vscan, self.viewpoint)
            if t != 0:
                tp = self.solver_dist[0]
                if tp < self.tmin[0]:
                    self.solve_one_or_network(1, head)

        self.trace_or_matrix(ofs + 1, or_network)

    def tracer(self, viewpoint, vscan):
        self.tmin[0] = 1000000000.0
        self.trace_or_matrix(0, self.or_net[0])
        t = self.tmin[0]
        return -0.1 < t < 100000000.0

    def write_rgb(self):
        red = int(self.rgb[0])
        red = min(255, max(0, red))

        green = int(self.rgb[1])
        green = min(255, max(0, green))

        blue = int(self.rgb[2])
        blue = min(255, max(0, blue))

        return (red, green, blue)

    def scan_point(self, scanx):
        if scanx >= self.size[0]:
            return []

        sscanx = (float(scanx) - self.scan_offset[0]) * self.scan_d[0]

        self.vscan[0] = sscanx * self.cos_v[1] + self.wscan[0]
        self.vscan[1] = self.scan_sscany[0] * self.cos_v[0] - self.vp[1]
        self.vscan[2] = -sscanx * self.sin_v[1] + self.wscan[2]

        metric = math.sqrt(self.fsqr(sscanx) + self.scan_met1[0])
        self.vscan[0] /= metric
        self.vscan[1] /= metric
        self.vscan[2] /= metric

        self.viewpoint[0] = self.view[0]
        self.viewpoint[1] = self.view[1]
        self.viewpoint[2] = self.view[2]

        self.rgb[0] = 0.0
        self.rgb[1] = 0.0
        self.rgb[2] = 0.0

        self.raytracing(0, 1.0)

        pixel = self.write_rgb()
        return [pixel] + self.scan_point(scanx + 1)

    def scan_line(self, scany):
        if scany >= self.size[1]:
            return []

        if scany % 10 == 0:
            print(f"Rendering line {scany}/{self.size[1]}...", file=sys.stderr)

        self.scan_sscany[0] = (self.scan_offset[0] - 1.0 - float(scany)) * self.scan_d[0]
        self.scan_met1[0] = self.fsqr(self.scan_sscany[0]) + 40000.0

        t1 = self.scan_sscany[0] * self.sin_v[0]
        self.wscan[0] = t1 * self.sin_v[1] - self.vp[0]
        self.wscan[2] = t1 * self.cos_v[1] - self.vp[2]

        pixels = self.scan_point(0)
        return pixels + self.scan_line(scany + 1)

    def scan_start(self):
        sizex = float(self.size[0])
        self.scan_d[0] = 128.0 / sizex
        self.scan_offset[0] = sizex / 2.0
        return self.scan_line(0)

    def rt(self, size_x, size_y):
        self.size[0] = size_x
        self.size[1] = size_y
        pixels = self.scan_start()
        return pixels


def parse_sld_file(filename):
    data = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            tokens = line.split()
            for token in tokens:
                try:
                    val = int(token)
                    data.append(float(val))
                except ValueError:
                    try:
                        val = float(token)
                        data.append(val)
                    except ValueError:
                        pass
    return data


def write_ppm(pixels, width, height, filename):
    with open(filename, 'wb') as f:
        f.write(b'P6\n')
        f.write(f'{width} {height}\n'.encode())
        f.write(b'255\n')
        for r, g, b in pixels:
            f.write(bytes([r, g, b]))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: minrt_correct.py <input.sld> <output.ppm> [width] [height]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 64
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 64

    print(f"Loading scene from {input_file}...")
    scene_data = parse_sld_file(input_file)
    print(f"Loaded {len(scene_data)} values")

    rt = MinRT()
    rt.read_parameter(scene_data)
    print(f"Loaded {len(rt.objects)} objects")

    print(f"Rendering {width}x{height}...")
    pixels = rt.rt(width, height)

    print(f"Writing output to {output_file}...")
    write_ppm(pixels, width, height, output_file)

    print("Done!")
