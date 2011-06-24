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

import gobject
import gtk

from kiwi.datatypes import ValueUnset
from kiwi.ui.proxywidget import ProxyWidgetMixin
from kiwi.utils import gsignal, type_register


class ProxyColorButton(gtk.ColorButton, ProxyWidgetMixin):
    __gtype_name__ = 'ProxyColorButton'

    data_type = gobject.property(
        getter=ProxyWidgetMixin.get_data_type,
        setter=ProxyWidgetMixin.set_data_type,
        type=str, blurb='Data Type')
    model_attribute = gobject.property(type=str, blurb='Model attribute')
    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)

    allowed_data_types = str,

    def __init__(self, color=gtk.gdk.Color(0, 0, 0)):
        ProxyWidgetMixin.__init__(self)
        gtk.ColorButton.__init__(self, color)

    gsignal('color-set', 'override')
    def do_color_set(self):
        self.emit('content-changed')
        self.chain()

    def read(self):
        color = self.get_color()
        return '#%02x%02x%02x' % (color.red / 256,
                                  color.green / 256,
                                  color.blue / 256)

    def update(self, data):
        if data is ValueUnset or data is None:
            data = 'black'
        color = gtk.gdk.color_parse(data)
        self.set_color(color)


type_register(ProxyColorButton)
