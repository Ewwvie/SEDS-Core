import numpy as np
import moderngl_window as mglw

VERT = """
#version 330
in vec2 in_pos;
out vec2 uv;
void main() {
    uv = in_pos;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

class AtmosApp(mglw.WindowConfig):
    gl_version = (3, 3)
    window_size = (960, 540)
    resizable = False
    frag_shader = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        quad = np.array([
            -1, -1,   1, -1,  -1,  1,
             1, -1,   1,  1,  -1,  1,
        ], dtype='f4')
        vbo = self.ctx.buffer(quad.tobytes())
        self.prog = self.ctx.program(
            vertex_shader=VERT,
            fragment_shader=self.__class__.frag_shader,
        )
        self.vao = self.ctx.simple_vertex_array(self.prog, vbo, 'in_pos')

    def render(self, time, frame_time):
        self.ctx.clear()
        if 'u_res' in self.prog:
            self.prog['u_res'].value = self.window_size
        if 'u_time' in self.prog:
            self.prog['u_time'].value = time
        self.vao.render()
        
        