# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307
# USA
#
# Author(s): Ali Afshar <aafshar@gmail.com>
#

"""ColorButton proxy for the kiwi framework"""

import gtk

from kiwi.ui.proxywidget import ProxyWidgetMixin
from kiwi.utils import PropertyObject, gsignal, type_register


class ProxyColorButton(PropertyObject, gtk.ColorButton, ProxyWidgetMixin):
    __gtype_name__ = 'ProxyColorButton'

    allowed_data_types = object,

    def __init__(self, color=gtk.gdk.Color(0, 0, 0)):
        ProxyWidgetMixin.__init__(self)
        PropertyObject.__init__(self, data_type=object)
        gtk.ColorButton.__init__(self, color)

    gsignal('color-set', 'override')
    def do_color_set(self):
        self.emit('content-changed')
        self.chain()

    def read(self):
        return self.get_color()

    def update(self, data):
        self.set_color(data)


type_register(ProxyColorButton)
